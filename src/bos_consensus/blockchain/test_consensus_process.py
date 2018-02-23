from ..common import Ballot, Message
from ..consensus import get_fba_module
from ..consensus.fba.isaac import IsaacState
from .util import blockchain_factory


IsaacConsensus = get_fba_module('isaac').IsaacConsensus


def test_state_lifecycle():
    node_name_1 = 'http://localhost:5001'
    node_name_2 = 'http://localhost:5002'
    node_name_3 = 'http://localhost:5003'

    bc1 = blockchain_factory(
        node_name_1,
        'http://localhost:5001',
        100,
        [node_name_2, node_name_3],
    )

    bc2 = blockchain_factory(
        node_name_2,
        'http://localhost:5002',
        100,
        [node_name_1, node_name_3],
    )

    bc3 = blockchain_factory(
        node_name_3,
        'http://localhost:5003',
        100,
        [node_name_1, node_name_2],
    )

    bc1.consensus.add_to_validator_connected(bc2.node)
    bc1.consensus.add_to_validator_connected(bc3.node)
    bc1.consensus.init()

    bc2.consensus.add_to_validator_connected(bc1.node)
    bc2.consensus.add_to_validator_connected(bc3.node)
    bc2.consensus.init()

    bc3.consensus.add_to_validator_connected(bc1.node)
    bc3.consensus.add_to_validator_connected(bc2.node)
    bc3.consensus.init()

    message = Message.new('message')
    ballot_init_1 = Ballot.new(node_name_1, message, IsaacState.INIT)
    ballot_init_2 = Ballot.new(node_name_2, message, IsaacState.INIT)
    ballot_init_3 = Ballot.new(node_name_3, message, IsaacState.INIT)

    bc1.receive_ballot(ballot_init_1)
    assert bc1.consensus.validator_ballots[bc1.node_name].state == IsaacState.INIT
    bc1.receive_ballot(ballot_init_2)
    assert bc1.consensus.validator_ballots[bc2.node_name].state == IsaacState.INIT
    bc1.receive_ballot(ballot_init_3)
    assert bc1.consensus.validator_ballots[bc3.node_name].state == IsaacState.INIT

    assert bc1.consensus.validator_ballots[bc1.node_name].state == IsaacState.SIGN
    assert bc1.get_state() == IsaacState.SIGN

    bc2.receive_ballot(ballot_init_1)
    bc2.receive_ballot(ballot_init_2)
    bc2.receive_ballot(ballot_init_3)

    bc3.receive_ballot(ballot_init_1)
    bc3.receive_ballot(ballot_init_2)
    bc3.receive_ballot(ballot_init_3)

    ballot_sign_1 = Ballot.new(node_name_1, message, IsaacState.SIGN)
    ballot_sign_2 = Ballot.new(node_name_2, message, IsaacState.SIGN)
    ballot_sign_3 = Ballot.new(node_name_3, message, IsaacState.SIGN)

    bc1.receive_ballot(ballot_sign_1)
    assert bc1.consensus.validator_ballots[bc1.node_name].state == IsaacState.SIGN
    bc1.receive_ballot(ballot_sign_2)
    assert bc1.consensus.validator_ballots[bc2.node_name].state == IsaacState.SIGN
    bc1.receive_ballot(ballot_sign_3)
    assert bc1.consensus.validator_ballots[bc3.node_name].state == IsaacState.SIGN
    assert bc1.consensus.validator_ballots[bc1.node_name].state == IsaacState.ACCEPT

    bc2.receive_ballot(ballot_sign_1)
    bc2.receive_ballot(ballot_sign_2)
    bc2.receive_ballot(ballot_sign_3)

    bc3.receive_ballot(ballot_sign_1)
    bc3.receive_ballot(ballot_sign_2)
    bc3.receive_ballot(ballot_sign_3)

    assert bc1.get_state() == IsaacState.ACCEPT
    assert bc2.get_state() == IsaacState.ACCEPT
    assert bc3.get_state() == IsaacState.ACCEPT

    ballot_accept_1 = Ballot.new(node_name_1, message, IsaacState.ACCEPT)
    ballot_accept_2 = Ballot.new(node_name_2, message, IsaacState.ACCEPT)
    ballot_accept_3 = Ballot.new(node_name_3, message, IsaacState.ACCEPT)

    bc1.receive_ballot(ballot_sign_1)    # different state ballot
    assert bc1.consensus.validator_ballots[bc1.node_name].state == IsaacState.ACCEPT
    assert bc1.consensus.validator_ballots[bc2.node_name].state == IsaacState.SIGN
    bc1.receive_ballot(ballot_accept_2)
    assert bc1.consensus.validator_ballots[bc2.node_name].state == IsaacState.ACCEPT
    bc1.receive_ballot(ballot_accept_3)
    assert bc1.consensus.validator_ballots[bc3.node_name].state == IsaacState.ACCEPT
    assert bc1.consensus.validator_ballots[bc1.node_name].state == IsaacState.ALLCONFIRM

    bc2.receive_ballot(ballot_accept_1)
    bc2.receive_ballot(ballot_accept_2)
    bc2.receive_ballot(ballot_sign_3)    # different state ballot

    bc3.receive_ballot(ballot_accept_1)
    bc3.receive_ballot(ballot_accept_2)
    bc3.receive_ballot(ballot_accept_3)

    assert bc1.get_state() == IsaacState.ALLCONFIRM
    assert bc2.get_state() == IsaacState.ACCEPT
    assert bc3.get_state() == IsaacState.ALLCONFIRM