# Copyright (C) 2009-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
#
# This file is part of the Prelude-Correlator program.
#
# SPDX-License-Identifier: BSD-2-Clause
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIEDi
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import sys
import os
import time
import signal
import pkg_resources
import errno
import itertools
import json

from prelude import ClientEasy, checkVersion
from preludecorrelator import idmef, pluginmanager, context, log, config, require, error

try:
    import kafka
except ImportError:
    kafka = None


if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins


logger = log.getLogger(__name__)
VERSION = pkg_resources.get_distribution('prelude-correlator').version
LIBPRELUDE_REQUIRED_VERSION = "1.2.6"
_DEFAULT_PROFILE = "prelude-correlator"


def _init_profile_dir(profile):
    filename = require.get_data_filename("context.dat", profile=profile)

    try:
        os.makedirs(os.path.dirname(filename), mode=0o700)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class Env:
    def __init__(self, options):
        self.prelude_client = None

        log.initLogger(options)
        self.config = config.Config(options.config)
        self.profile = options.profile

    def load_plugins(self):
        self.pluginmanager = pluginmanager.PluginManager()

        # restore previous context
        # (this need to be called after logger is setup, and before plugin loading).
        context.load(self.profile)

        # Since we can launch different instances of prelude-correlator with different profiles,
        # we need to separate their context and specific rules data files
        # (this need to be called before plugin loading)
        _init_profile_dir(self.profile)

        self.pluginmanager.load()
        self.pluginmanager.check_dependencies()
        logger.info("%d plugins have been loaded.", self.pluginmanager.getPluginCount())


class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGQUIT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info("caught signal %d", signum)
        env.pluginmanager.signal(signum, frame)

        if signum == signal.SIGUSR1:
            context.save(env.profile)
            env.pluginmanager.save()

        elif signum == signal.SIGQUIT:
            context.stats()
            env.pluginmanager.stats()

            if env.prelude_client:
                env.prelude_client.stats()

        else:
            env.prelude_client.stop()


class GenericReader(object):
    _messages = iter([])

    def run(self):
        pass

    def stop(self):
        pass

    def inject(self, idmef):
        self._messages = itertools.chain(self._messages, [idmef])


class ClientReader(GenericReader):
    def __init__(self, prelude_client):
        self.prelude_client = prelude_client

    def run(self):
        while True:
            for msg in self._messages:
                yield msg

            msg = idmef.IDMEF()
            try:
                ret = self.prelude_client.client.recvIDMEF(msg, 1000)
            except Exception:
                ret = None

            if ret:
                yield msg
            else:
                yield None


class FileReader(GenericReader):
    def __init__(self, filename, offset=0, limit=-1):
        self.filename = filename
        self.offset = offset
        self.limit = limit

    def run(self):
        count = 0

        with open(self.filename, 'r') as input_file:
            while self.limit == -1 or count < self.limit + self.offset:
                for msg in self._messages:
                    yield msg

                msg = idmef.IDMEF()
                try:
                    msg << input_file
                except EOFError:
                    break

                count += 1

                if count >= self.offset:
                    yield msg


class KafkaReader(GenericReader):
    def __init__(self, prelude_client, server, topic, profile):
        options = {
            'bootstrap_servers': server,
            'group_id': profile,
            'value_deserializer': lambda v: json.loads(v.decode('utf-8')),
        }
        self.client = kafka.KafkaConsumer(topic, **options)
        self.prelude_client = prelude_client

    def run(self):
        while True:
            for msg in self._messages:
                yield msg

            ret = self.client.poll(1000)
            if not ret:
                yield None

            for topic, messages in ret.items():
                for data in messages:
                    try:
                        yield idmef.IDMEF(data.value)
                    except RuntimeError:
                        pass

    def stop(self):
        self.client.close()


class ClientWriter(object):
    def __init__(self, prelude_client):
        self.prelude_client = prelude_client

    def send(self, idmef):
        self.prelude_client.client.sendIDMEF(idmef)


class KafkaWriter(object):
    def __init__(self, server, topic):
        self._topic = topic

        options = {
            'bootstrap_servers': server,
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
        }
        self.client = kafka.KafkaProducer(**options)

    def send(self, idmef):
        self.client.send(self._topic, value=idmef.obj)


class PreludeClient(object):
    def __init__(self, options, print_input=None, print_output=None, dry_run=False):
        self._events_processed = 0
        self._alert_generated = 0
        self._print_input = print_input
        self._print_output = print_output
        self._continue = True
        self._dry_run = dry_run
        self._grouping = env.config.get("general", "grouping")

        if kafka and options.kafka_server:
            self._receiver = KafkaReader(self, options.kafka_server, options.kafka_consumer_topic, options.profile)
            self._sender = KafkaWriter(options.kafka_server, options.kafka_producer_topic)
            return

        if not options.input_file:
            self._receiver = ClientReader(self)
        else:
            self._receiver = FileReader(options.input_file, options.input_offset, options.input_limit)

        self.client = ClientEasy(
            options.profile, ClientEasy.PERMISSION_IDMEF_READ | ClientEasy.PERMISSION_IDMEF_WRITE,
            "Prelude Correlator", "Correlator", "CS GROUP", VERSION)

        self.client.setConfigFilename(options.config)
        self.client.start()

        self._sender = ClientWriter(self)

    def _handle_event(self, idmef):
        if self._print_input:
            self._print_input.write(str(idmef))

        env.pluginmanager.run(idmef)
        self._events_processed += 1

    def stats(self):
        logger.info("%d events received, %d correlationAlerts generated.",
                    self._events_processed,
                    self._alert_generated)

    def get_grouping(self, idmef):
        if self._grouping:
            value = idmef.get(self._grouping)
            if isinstance(value, list):
                value = value[0]
        else:
            value = None

        return self._grouping, value

    def correlationAlert(self, idmef):
        self._alert_generated = self._alert_generated + 1

        if not self._dry_run:
            self._sender.send(idmef)

        if self._print_output:
            self._print_output.write(str(idmef))

        # Reinject correlation alerts for meta-correlation
        #self._receiver.inject(idmef)

    def run(self):
        last = time.time()
        for msg in self._receiver.run():
            if msg:
                self._handle_event(msg)

            now = time.time()
            if now - last >= 1:
                context.wakeup(now)
                last = now

            if not self._continue:
                break

    def stop(self):
        self._continue = False
        self._receiver.stop()


def runCorrelator():
    checkVersion(LIBPRELUDE_REQUIRED_VERSION)
    config_filename = require.get_config_filename("prelude-correlator.conf")

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", default=config_filename, metavar="FILE", help="Configuration file to use")
    parser.add_argument("--dry-run", action="store_true", help="No report to the specified Manager will occur")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("-P", "--pidfile", metavar="FILE", help="Write Prelude Correlator PID to specified file")
    parser.add_argument("--print-input", metavar="FILE", help="Dump alert input from manager to the specified file")
    parser.add_argument("--print-output", metavar="FILE", help="Dump alert output to the specified file")
    parser.add_argument("-D", "--debug", type=int, default=0, metavar="LEVEL", nargs="?", const=1,
                        help="Enable debugging output (level from 1 to 10)")
    parser.add_argument("-v", "--version", action="version", version=VERSION)

    group = parser.add_argument_group("IDMEF Input", "Read IDMEF events from file")
    group.add_argument("--input-file", metavar="FILE", help="Read IDMEF events from the specified file")
    group.add_argument("--input-offset", type=int, default=0, metavar="OFFSET",
                       help="Start processing events starting at the given offset")
    group.add_argument("--input-limit", type=int, default=-1, metavar="LIMIT",
                       help="Read events until the given limit is reached")

    group = parser.add_argument_group("Prelude", "Prelude generic options")
    group.add_argument("--profile", default=_DEFAULT_PROFILE, help="Profile to use for this analyzer")

    if kafka:
        group = parser.add_argument_group("Kafka Input", "Read IDMEF events from an Apache Kafka broker")
        group.add_argument("--kafka-server", metavar="SERVER", help="Kafka bootstrap server")
        group.add_argument("--kafka-consumer-topic", default="prelude", metavar="TOPIC", help="Kafka consumer topic")
        group.add_argument("--kafka-producer-topic", default="prelude", metavar="TOPIC", help="Kafka producer topic")

    options = parser.parse_args()

    builtins.env = Env(options)
    env.load_plugins()
    SignalHandler()

    ifd = None
    if options.print_input:
        if options.print_input == "-":
            ifd = sys.stdout
        else:
            ifd = open(options.print_input, "w")

    ofd = None
    if options.print_output:
        if options.print_output == "-":
            ofd = sys.stdout
        else:
            ofd = open(options.print_output, "w")

    if options.daemon:
        if os.fork():
            os._exit(0)

        os.setsid()
        if os.fork():
            os._exit(0)

        os.umask(0o77)

        fd = os.open('/dev/null', os.O_RDWR)
        for i in range(3):
            os.dup2(fd, i)

        os.close(fd)
        if options.pidfile:
            open(options.pidfile, "w").write(str(os.getpid()))

    try:
        env.prelude_client = PreludeClient(options, print_input=ifd, print_output=ofd)
    except Exception as e:
        raise error.UserError(e)

    idmef.set_prelude_client(env.prelude_client)

    env.prelude_client.run()

    # save existing context
    context.save(options.profile)
    env.pluginmanager.save()


def main():
    try:
        runCorrelator()

    except error.UserError as e:
        logger.error("error caught while starting prelude-correlator : %s", e)
        sys.exit(1)

    except:
        raise
