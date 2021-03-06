import sqlite3

import pytest
from dhalsim.python2.generic_scada import GenericScada, DatabaseError
from mock import call


@pytest.fixture
def patched_scada(mocker):
    sleeper = mocker.patch("time.sleep", return_value=None)
    mocker.patch.object(GenericScada, "__init__", return_value=None)
    mocker.patch.object(GenericScada, "DB_TRIES", 3)
    mocker.patch.object(GenericScada, "DB_SLEEP_TIME", 1.5)
    cur_mock = mocker.Mock()
    conn_mock = mocker.Mock()
    logger_mock = mocker.Mock()

    scada = GenericScada()
    scada.cur = cur_mock
    scada.conn = conn_mock
    scada.logger = logger_mock

    return scada, cur_mock, conn_mock, logger_mock, sleeper

def test_get_master_clock_first_try(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.fetchone.return_value = [5]

    assert scada.get_master_clock() == 5

    cur_mock.execute.assert_called_once_with("SELECT time FROM master_time WHERE id IS 1")

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_get_master_clock_fail_once(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    cur_mock.fetchone.return_value = [5]

    assert scada.get_master_clock() == 5

    cur_mock.execute.assert_has_calls([call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1")])
    assert cur_mock.execute.call_count == 2

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_get_master_clock_fail_all(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        scada.get_master_clock()

    cur_mock.execute.assert_has_calls([call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1")])
    assert cur_mock.execute.call_count == 3

    cur_mock.fetchone.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5), call(1.5), call(1.5)])
    assert sleeper.call_count == 3

def test_get_sync_first_try(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.fetchone.return_value = [1]

    assert scada.get_sync() is True

    cur_mock.execute.assert_called_once_with("SELECT flag FROM sync WHERE name IS 'scada'")

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_get_sync_fail_once(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    cur_mock.fetchone.return_value = [1]

    assert scada.get_sync() is True

    cur_mock.execute.assert_has_calls([call("SELECT flag FROM sync WHERE name IS 'scada'"),
                                       call("SELECT flag FROM sync WHERE name IS 'scada'")])
    assert cur_mock.execute.call_count == 2

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_get_sync_fail_all(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        scada.get_sync()

    cur_mock.execute.assert_has_calls([call("SELECT flag FROM sync WHERE name IS 'scada'"),
                                       call("SELECT flag FROM sync WHERE name IS 'scada'"),
                                       call("SELECT flag FROM sync WHERE name IS 'scada'")])
    assert cur_mock.execute.call_count == 3

    cur_mock.fetchone.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5), call(1.5), call(1.5)])
    assert sleeper.call_count == 3


def test_set_sync_first_try(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    scada.set_sync(True)

    cur_mock.execute.assert_called_once_with("UPDATE sync SET flag=? WHERE name IS 'scada'", (1,))

    conn_mock.commit.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_set_sync_fail_once(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    scada.set_sync(True)

    cur_mock.execute.assert_has_calls([call("UPDATE sync SET flag=? WHERE name IS 'scada'", (1,)),
                                       call("UPDATE sync SET flag=? WHERE name IS 'scada'", (1,))])
    assert cur_mock.execute.call_count == 2

    conn_mock.commit.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_set_sync_fail_all(patched_scada):
    scada, cur_mock, conn_mock, logger_mock, sleeper = patched_scada

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        scada.set_sync(True)

    cur_mock.execute.assert_has_calls([call("UPDATE sync SET flag=? WHERE name IS 'scada'", (1,)),
                                       call("UPDATE sync SET flag=? WHERE name IS 'scada'", (1,)),
                                       call("UPDATE sync SET flag=? WHERE name IS 'scada'", (1,))])
    assert cur_mock.execute.call_count == 3

    conn_mock.commit.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5), call(1.5), call(1.5)])
    assert sleeper.call_count == 3
