# -*- coding: latin-1 -*-
import pytest
import datetime import datetime

from piecash import Account, Commodity, Split, Transaction
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic

# dummy line to avoid removing unused symbols

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri


class TestAccount_create_account(object):
    def test_create_parentless_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create an account without parent that is not ROOT
        acc = Account(name="test account", type="ASSET", commodity=EUR)
        new_book.add(acc)
        with pytest.raises(ValueError):
            new_book.validate()
        new_book.cancel()

        # create an account without parent that is ROOT but with wrong name
        acc = Account(name="test account", type="ROOT", commodity=EUR)
        new_book.add(acc)
        with pytest.raises(ValueError):
            new_book.validate()
        new_book.cancel()

        # create an account without parent that is ROOT with correct name
        acc = Account(name="Root Account", type="ROOT", commodity=EUR)
        new_book.add(acc)
        new_book.flush()

        assert len(new_book.accounts) == 0
        root_accs = new_book.query(Account).all()
        assert len(root_accs) == 3

    def test_create_samenameandparent_accounts(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account
        acc1 = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        acc2 = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        with pytest.raises(ValueError):
            new_book.validate()

    def test_create_samenameanddifferentparent_accounts(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create 2 accounts with same name but different parent
        acc1 = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        acc2 = Account(name="test account", type="ASSET", commodity=EUR, parent=acc1)
        new_book.flush()
        assert acc1.fullname == "test account"
        assert acc2.fullname == "test account:test account"

    def test_create_standardasset_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        new_book.flush()
        assert len(new_book.accounts) == 1
        assert acc.non_std_scu == 0
        assert acc.commodity_scu == EUR.fraction
        assert acc.get_balance() == 0
        assert acc.get_balance(at_date=datetime.date.today()) == 0
        assert acc.sign == 1
        assert not acc.is_template

    def test_account_balance_on_date(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        e = book_basic.accounts(name="exp")

        splits = [
            Split(account=a, value=100, memo=u"m�mo asset"),
            Split(account=e, value=-100, memo=u"m�mo exp"),
        ]

        with pytest.raises(ValueError):
            tr = Transaction(currency=EUR, description=u"wire from H�l�ne", notes=u"on St-Eug�ne day",
                             post_date=datetime(2014, 1, 1),
                             enter_date=datetime(2014, 1, 1),
                             splits=splits)

        with pytest.raises(ValueError):
            tr = Transaction(currency=EUR, description=u"wire from H�l�ne", notes=u"on St-Eug�ne day",
                             post_date=datetime(2014, 1, 2),
                             enter_date=datetime(2014, 1, 2),
                             splits=splits)

        with pytest.raises(ValueError):
            tr = Transaction(currency=EUR, description=u"wire from H�l�ne", notes=u"on St-Eug�ne day",
                             post_date=datetime(2014, 1, 3),
                             enter_date=datetime(2014, 1, 3),
                             splits=splits)

        book_basic.flush()

        assert acc.get_balance(at_date=datetime(2014, 1, 1)) == 100
        assert acc.get_balance(at_date=datetime(2014, 1, 2)) == 200
        assert acc.get_balance(at_date=datetime(2014, 1, 3)) == 300
        assert acc.get_balance(at_date=datetime(2014, 1, 4)) == 300


    def test_create_standardliability_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name="test account", type="LIABILITY", commodity=EUR, parent=racc)
        new_book.flush()
        assert len(new_book.accounts) == 1
        assert acc.non_std_scu == 0
        assert acc.commodity_scu == EUR.fraction
        assert acc.get_balance() == 0
        assert acc.sign == -1
        assert not acc.is_template

    def test_create_unknowntype_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create account with unknown type
        with pytest.raises(ValueError):
            acc = Account(name="test account", type="FOO", commodity=EUR, parent=racc)
            new_book.validate()

    def test_create_nobook_account(self, new_book):
        USD = Commodity(namespace="FOO", mnemonic="BAZ", fullname="cuz")

        # create account with no book attachable to it
        with pytest.raises(ValueError):
            acc = Account(name="test account", type="ASSET", commodity=USD)
            new_book.flush()

    def test_create_children_accounts(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create account with unknown type
        acc = Account(name="test account", type="ASSET", commodity=EUR, parent=racc,
                      children=[Account(name="test sub-account", type="ASSET", commodity=EUR)])
        new_book.flush()
        assert len(acc.children) == 1

    def test_create_unicodename_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name=u"inou� �trange", type="ASSET", commodity=EUR, parent=racc)
        new_book.flush()
        assert len(new_book.accounts) == 1
        assert len(repr(acc)) >= 2

    def test_create_root_subaccount(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create root account should raise an exception
        acc = Account(name="subroot accout", type="ROOT", commodity=EUR, parent=racc)
        with pytest.raises(ValueError):
            new_book.validate()

        # except if we add the control_mode 'allow-root-subaccounts' to the book
        new_book.control_mode.append("allow-root-subaccounts")
        new_book.validate()

        assert len(new_book.accounts) == 1


class TestAccount_features(object):
    def test_sign_accounts(self, new_book):
        EUR = new_book.commodities[0]
        neg = "EQUITY,PAYABLE,LIABILITY,CREDIT,INCOME".split(",")
        pos = "STOCK,MUTUAL,EXPENSE,BANK,TRADING,CASH,ASSET,RECEIVABLE".split(",")
        all = neg + pos
        for acc in all:
            assert Account(name=acc, type=acc, commodity=EUR).sign == (1 if acc in pos else -1)

    def test_scu(self, new_book):
        EUR = new_book.commodities[0]
        acc = Account(name="test", type="ASSET", commodity=EUR)
        assert acc.commodity_scu == EUR.fraction
        assert not acc.non_std_scu
        acc.commodity_scu = 100
        assert acc.non_std_scu
        acc.commodity_scu = None
        assert acc.commodity_scu == EUR.fraction
        assert not acc.non_std_scu
