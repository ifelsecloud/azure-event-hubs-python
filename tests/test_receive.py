#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import pytest

from azure import eventhub
from azure.eventhub import EventData, EventHubClient, Offset


def test_receive_single_event(connection_str, senders):
    senders[0].send(EventData(b"Receiving a single event"))

    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0")
    client.run()
    messages = []
    received = receiver.receive(timeout=2)
    while received:
        messages.extend(received)
        received = receiver.receive(timeout=2)

    assert len(messages) >= 1
    assert list(messages[-1].body)[0] == b"Receiving a single event"
    client.stop()


def test_receive_end_of_stream(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Receiving only a single event"))
    received = receiver.receive(timeout=2)
    assert len(received) == 1

    assert list(received[-1].body)[0] == b"Receiving only a single event"
    client.stop()


def test_receive_with_offset(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Data"))
    received = receiver.receive(timeout=2)
    assert len(received) == 1
    offset = received[0].offset

    offset_receiver = client.add_receiver("$default", "0", offset=Offset(offset))
    client.run()
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Message after offset"))
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 1
    client.stop()


def test_receive_with_inclusive_offset(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Data"))
    received = receiver.receive(timeout=2)
    assert len(received) == 1
    offset = received[0].offset

    offset_receiver = client.add_receiver("$default", "0", offset=Offset(offset, inclusive=True))
    client.run()
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 1
    client.stop()


def test_receive_with_datetime(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Data"))
    received = receiver.receive(timeout=2)
    assert len(received) == 1
    offset = received[0].enqueued_time

    offset_receiver = client.add_receiver("$default", "0", offset=Offset(offset))
    client.run()
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Message after timestamp"))
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 1
    client.stop()


def test_receive_with_sequence_no(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Data"))
    received = receiver.receive(timeout=2)
    assert len(received) == 1
    offset = received[0].sequence_number

    offset_receiver = client.add_receiver("$default", "0", offset=Offset(offset))
    client.run()
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Message next in sequence"))
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 1
    client.stop()


def test_receive_with_inclusive_sequence_no(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    senders[0].send(EventData(b"Data"))
    received = receiver.receive(timeout=2)
    assert len(received) == 1
    offset = received[0].sequence_number

    offset_receiver = client.add_receiver("$default", "0", offset=Offset(offset, inclusive=True))
    client.run()
    received = offset_receiver.receive(timeout=2)
    assert len(received) == 1
    client.stop()


def test_receive_batch(connection_str, senders):
    client = EventHubClient.from_connection_string(connection_str, debug=False)
    receiver = client.add_receiver("$default", "0", prefetch=500, offset=Offset('@latest'))
    client.run()

    received = receiver.receive(timeout=2)
    assert len(received) == 0
    for i in range(10):
        senders[0].send(EventData(b"Data"))
    received = receiver.receive(max_batch_size=5, timeout=2)
    assert len(received) == 5
    client.stop()

