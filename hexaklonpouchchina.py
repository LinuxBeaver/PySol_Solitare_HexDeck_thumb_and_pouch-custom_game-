#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------##
#
# Copyright (C) 1998-2003 Markus Franz Xaver Johannes Oberhumer
# Copyright (C) 2003 Mt. Hood Playing Card Co.
# Copyright (C) 2005-2009 Skomoroh
# 2023 Beaver, mod to play Thumb and Pouch variations of the hex deck games
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------##

# Imports
import math

from pysollib.game import Game
from pysollib.gamedb import GI, GameInfo, registerGame
from pysollib.games.montana import Montana, Montana_RowStack
from pysollib.hint import CautiousDefaultHint, DefaultHint
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.mygettext import _
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import \
        BO_RowStack, \
        AbstractFoundationStack, \
        BasicRowStack, \
        InitialDealTalonStack, \
        OpenStack, \
        ReserveStack, \
        SS_FoundationStack, \
        BO_RowStack, \
        StackWrapper, \
        WasteStack, \
        WasteTalonStack, \
        Yukon_BO_RowStack
from pysollib.util import ANY_RANK, ANY_SUIT, NO_RANK, UNLIMITED_ACCEPTS, \
        UNLIMITED_MOVES

# ************************************************************************
# * Hex A Deck Foundation Stacks
# ************************************************************************


class HexADeck_FoundationStack(SS_FoundationStack):
    def __init__(self, x, y, game, suit, **cap):
        kwdefault(cap, max_move=0, max_cards=12)
        SS_FoundationStack.__init__(self, x, y, game, suit, **cap)


class HexATrump_Foundation(HexADeck_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not self.basicAcceptsCards(from_stack, cards):
            return 0
        for s in self.game.s.foundations[:3]:
            if len(s.cards) != 16:
                return 0
        return 1


class Merlins_Foundation(AbstractFoundationStack):
    def __init__(self, x, y, game, suit, **cap):
        kwdefault(cap, mod=16, dir=0, base_rank=NO_RANK, max_move=0)
        AbstractFoundationStack.__init__(self, x, y, game, suit, **cap)

    def acceptsCards(self, from_stack, cards):
        if not AbstractFoundationStack.acceptsCards(self, from_stack, cards):
            return 0
        if not self.cards:
            return 1
        stack_dir = self.game.getFoundationDir()
        if stack_dir == 0:
            card_dir = (cards[0].rank - self.cards[-1].rank) % self.cap.mod
            return card_dir in (1, 15)
        else:
            return (self.cards[-1].rank + stack_dir) % self.cap.mod \
                == cards[0].rank


# ************************************************************************
# * Hex A Deck Row Stacks
# ************************************************************************

class HexADeck_OpenStack(OpenStack):

    def __init__(self, x, y, game, yoffset, **cap):
        kwdefault(cap, max_move=UNLIMITED_MOVES, max_accept=UNLIMITED_ACCEPTS,
                  dir=-1)
        OpenStack.__init__(self, x, y, game, **cap)
        self.CARD_YOFFSET = yoffset

    def isRankSequence(self, cards, dir=None):
        if not dir:
            dir = self.cap.dir
        c1 = cards[0]
        for c2 in cards[1:]:
            if not c1.rank + dir == c2.rank:
                return 0
            c1 = c2
        return 1

    def isAlternateColorSequence(self, cards, dir=None):
        if not dir:
            dir = self.cap.dir
        c1 = cards[0]
        for c2 in cards[1:]:
            if (c1.color < 2 and c1.color == c2.color or
                    not c1.rank + dir == c2.rank):
                return 0
            c1 = c2
        return 1

    def isSuitSequence(self, cards, dir=None):
        if not dir:
            dir = self.cap.dir
        c1 = cards[0]
        for c2 in cards[1:]:
            if not ((c1.color == 2 or c2.color == 2 or c1.suit == c2.suit) and
                    c1.rank + dir == c2.rank):
                return 0
            c1 = c2
        return 1


class HexADeck_RK_RowStack(HexADeck_OpenStack):

    def acceptsCards(self, from_stack, cards):
        if (not self.basicAcceptsCards(from_stack, cards) or
                not self.isRankSequence(cards)):
            return 0
        if not self.cards:
            return cards[0].rank == 15 or self.cap.base_rank == ANY_RANK
        return self.isRankSequence([self.cards[-1], cards[0]])

    def canMoveCards(self, cards):
        return (self.basicCanMoveCards(cards) and self.isRankSequence(cards))


class HexADeck_BO_RowStack(HexADeck_OpenStack):

    def acceptsCards(self, from_stack, cards):
        if (not self.basicAcceptsCards(from_stack, cards) or
                not self.isAlternateColorSequence(cards)):
            return 0
        if not self.cards:
            return cards[0].rank == 15 or self.cap.base_rank == ANY_RANK
        return self.isAlternateColorSequence([self.cards[-1], cards[0]])

    def canMoveCards(self, cards):
        return (self.basicCanMoveCards(cards) and
                self.isAlternateColorSequence(cards))


class HexADeck_SS_RowStack(HexADeck_OpenStack):

    def acceptsCards(self, from_stack, cards):
        if (not self.basicAcceptsCards(from_stack, cards) or
                not self.isSuitSequence(cards)):
            return 0
        if not self.cards:
            return cards[0].rank == 15 or self.cap.base_rank == ANY_RANK
        return self.isSuitSequence([self.cards[-1], cards[0]])

    def canMoveCards(self, cards):
        return (self.basicCanMoveCards(cards) and self.isSuitSequence(cards))


class Bits_RowStack(ReserveStack):

    def acceptsCards(self, from_stack, cards):
        if not self.basicAcceptsCards(from_stack, cards):
            return 0
        stackcards = self.cards
        if stackcards or cards[0].suit == 4:
            return 0
        i = int(self.id // 4)
        for r in self.game.s.rows[i * 4:self.id]:
            if not r.cards:
                return 0
        return ((self.game.s.foundations[i].cards[-1].rank + 1 >>
                 (self.id % 4)) % 2 == (cards[0].rank + 1) % 2)


class Bytes_RowStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not self.basicAcceptsCards(from_stack, cards):
            return 0
        stackcards = self.cards
        if stackcards or cards[0].suit == 4:
            return 0
        id = self.id - 16
        i = int(id // 2)
        for r in self.game.s.rows[16 + i * 2:self.id]:
            if not r.cards:
                return 0
        return self.game.s.foundations[i].cards[-1].rank == cards[0].rank


class HexAKlon_RowStack(BO_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not self.basicAcceptsCards(from_stack, cards):
            return 0
        stackcards = self.cards
        if stackcards:
            if (stackcards[-1].suit == 4 or cards[0].suit == 4):
                return 1
        return BO_RowStack.acceptsCards(self, from_stack, cards)


class HexADeck_ACRowStack(BO_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not self.basicAcceptsCards(from_stack, cards):
            return 0
        stackcards = self.cards
        if stackcards:
            if (stackcards[-1].suit == 4 or cards[0].suit == 4):
                return stackcards[-1].rank == cards[0].rank + 1
        return BO_RowStack.acceptsCards(self, from_stack, cards)


class Familiar_ReserveStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not ReserveStack.acceptsCards(self, from_stack, cards):
            return 0
        # Only take Wizards
        return cards[0].suit == 4

    def getBottomImage(self):
        return self.game.app.images.getSuitBottom(4)


class Merlins_BraidStack(OpenStack):
    def __init__(self, x, y, game):
        OpenStack.__init__(self, x, y, game)
        self.CARD_YOFFSET = self.game.app.images.CARD_YOFFSET
        # use a sine wave for the x offsets
        self.CARD_XOFFSET = []
        j = 1
        for i in range(20):
            self.CARD_XOFFSET.append(int(math.sin(j) * 20))
            j = j + .9


class Merlins_RowStack(ReserveStack):
    def fillStack(self):
        if not self.cards and self.game.s.braid.cards:
            self.game.moveMove(1, self.game.s.braid, self)

    def getBottomImage(self):
        return self.game.app.images.getBraidBottom()


class Merlins_ReserveStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if from_stack is self.game.s.braid or from_stack in self.game.s.rows:
            return 0
        return ReserveStack.acceptsCards(self, from_stack, cards)

    def getBottomImage(self):
        return self.game.app.images.getTalonBottom()


# ************************************************************************
# *
# ************************************************************************

class AbstractHexADeckGame(Game):
    RANKS = (_("Ace"), "2", "3", "4", "5", "6", "7", "8", "9",
             "A", "B", "C", "D", "E", "F", "10")


class Merlins_Hint(DefaultHint):
    pass




# ************************************************************************
# * Hex A Klon (thumb and pouch style)
# ************************************************************************

class HexAKlon(Game):
    Hint_Class = CautiousDefaultHint
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = WasteTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = HexAKlon_RowStack

    #
    # Game layout
    #

    def createGame(self, max_rounds=-1, num_deal=1, **layout):
        l, s = Layout(self), self.s
        kwdefault(layout, rows=8, waste=1, playcards=20)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])

        # Create talon
        s.talon = self.Talon_Class(
            l.s.talon.x, l.s.talon.y, self,
            max_rounds=max_rounds, num_deal=num_deal)
        s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)

        # Create foundations
        for r in l.s.foundations[:4]:
            s.foundations.append(
                self.Foundation_Class(
                    r.x, r.y, self,
                    r.suit, mod=16, max_cards=16, max_move=1))
        r = l.s.foundations[4]
        s.foundations.append(
            HexATrump_Foundation(
                r.x, r.y, self, 4, mod=4,
                max_move=0, max_cards=4, base_rank=ANY_RANK))

        # Create rows
        for r in l.s.rows:
            s.rows.append(
                self.RowStack_Class(
                    r.x, r.y, self,
                    suit=ANY_SUIT, base_rank=15))

        # Define stack groups
        l.defaultAll()

    #
    # Game over rides
    #

    def startGame(self):
        assert len(self.s.talon.cards) == 68
        for i in range(len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i+1:], flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))

# ************************************************************************
# * Thumb and Pouch Plus 16
# ************************************************************************

class KlondikePlus16(Game):
    Hint_Class = CautiousDefaultHint
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = WasteTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = HexAKlon_RowStack

    #
    # Game layout
    #

    def createGame(self, max_rounds=2, num_deal=1, **layout):
        l, s = Layout(self), self.s
        kwdefault(layout, rows=8, waste=1, playcards=20)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])

        # Create talon
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self,
                                   max_rounds=max_rounds, num_deal=num_deal)
        s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)

        # Create foundations
        for r in l.s.foundations:
            s.foundations.append(
                self.Foundation_Class(
                    r.x, r.y, self,
                    r.suit, mod=16, max_cards=16, max_move=1))

        # Create rows
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self,
                                              suit=ANY_SUIT, base_rank=15))

        # Define stack groups
        l.defaultAll()

    #
    # Game over rides
    #

    def startGame(self):
        assert len(self.s.talon.cards) == 68
        for i in range(len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i+1:], flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# ************************************************************************
# *
# ************************************************************************


def r(id, gameclass, name, game_type, decks, redeals, skill_level):
    game_type = game_type | GI.GT_HEXADECK
    gi = GameInfo(id, gameclass, name, game_type, decks, redeals, skill_level,
                  suits=list(range(4)), ranks=list(range(16)),
                  trumps=list(range(4)))
    registerGame(gi)
    return gi


r(4742, HexAKlon, 'T & P Hex A Klon', GI.GT_HEXADECK, 1, -1, GI.SL_BALANCED)
r(6934, KlondikePlus16, 'Thumb and Pouch Plus 16', GI.GT_HEXADECK, 1, 1,
  GI.SL_BALANCED)
