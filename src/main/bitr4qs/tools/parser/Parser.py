import re
from src.main.bitr4qs.term.Triple import Triple
from src.main.bitr4qs.term.Quad import Quad
from src.main.bitr4qs.term.Modification import Modification
from src.main.bitr4qs.namespace import BITR4QS
from rdflib.plugins.parsers.ntriples import W3CNTriplesParser
from rdflib.term import URIRef
from rdflib.namespace import RDF, RDFS


class TripleSink(object):

    def __init__(self):
        self._subject = None
        self._predicate = None
        self._object = None

    def add_modification(self, graph=None, deletion=False):
        if graph is None:
            return Modification(Triple((self._subject, self._predicate, self._object)), deletion)
        else:
            return Modification(Quad((self._subject, self._predicate, self._object), graph), deletion)

    def triple(self, s, p, o):
        print("s ", s)
        print("p ", p)
        print("o ", o)
        self._subject = s
        self._predicate = p
        self._object = o

    @property
    def subject(self):
        return self._subject

    @property
    def predicate(self):
        return self._predicate

    @property
    def object(self):
        return self._object


class Parser(object):

    @classmethod
    def parse_sorted_implicit(cls, stringOfValidRevisions, forwards=True):
        """

        :param stringOfValidRevisions:
        :param forwards:
        :return:
        """
        validRevisions = cls.parse_revisions(stringOfValidRevisions, 'valid')
        listOfValidRevisions = list(validRevisions.values())
        reverse = False if forwards else True
        listOfValidRevisions.sort(key=lambda x: x.revision_number, reverse=reverse)
        orderedValidRevisions = dict(zip(list(range(len(listOfValidRevisions))), listOfValidRevisions))
        return orderedValidRevisions

    @classmethod
    def parse_sorted_explicit(cls, stringOfValidRevisions, stringOfTransactionRevisions, endRevision: URIRef,
                              forwards=True):
        """

        :param stringOfValidRevisions:
        :param stringOfTransactionRevisions:
        :param endRevision:
        :param forwards:
        :return:
        """
        transactionRevisions = cls.parse_revisions(stringOfTransactionRevisions, 'transaction')
        validRevisions = cls.parse_revisions(stringOfValidRevisions, 'valid')

        orderedValidRevisions = {}
        nOfRevisions = len(validRevisions)
        i = 0
        while i == nOfRevisions:
            if str(endRevision) in transactionRevisions:
                revision = transactionRevisions[str(endRevision)]
                endRevision = revision.preceding_revision

                if revision.valid_revision is not None:
                    validRevision = validRevisions[str(revision.valid_revision)]

                    if forwards:
                        j = nOfRevisions - i
                        orderedValidRevisions[j] = validRevision
                    else:
                        orderedValidRevisions[i] = validRevision

                    i += 1
        return orderedValidRevisions

    @classmethod
    def parse_revisions(cls, stringOfRevisions, revisionName):
        """

        :param stringOfRevisions:
        :param revisionName:
        :return:
        """
        revisions = {}

        functionName = "parse_" + revisionName + '_revision'
        func = getattr(cls, functionName)

        NQuads = stringOfRevisions.split('\n')[:-1]
        index = 0

        while index != len(NQuads):
            revisionID = re.findall(r'<(.*?)>', NQuads[index])[0]

            if revisionID in revisions:
                revision, index = func(revisionID, NQuads[index:], index, revisions[revisionID])
            else:
                revision, index = func(revisionID, NQuads[index:], index)

            revisions[str(revision.identifier)] = revision
        print("revisions ", revisions)
        return revisions

    @staticmethod
    def _get_valid_revision(identifier):
        from src.main.bitr4qs.revision.ValidRevision import ValidRevision
        return ValidRevision(URIRef(identifier))

    @staticmethod
    def _parse_valid_revision(revision, p, o):
        pass

    @classmethod
    def parse_valid_revision(cls, identifier, NTriples, index, revision=None):
        """

        :param identifier:
        :param NTriples:
        :param index:
        :param revision:
        :return:
        """
        if revision is None:
            revision = cls._get_valid_revision(identifier)

        sink = TripleSink()
        NTriplesParser = W3CNTriplesParser(sink=sink)

        for NTriple in NTriples:

            NTriplesParser.parsestring(NTriple)

            if identifier != str(sink.subject):
                return revision, index

            index += 1

            if str(sink.predicate) == str(BITR4QS.hash):
                revision.hexadecimal_of_hash = sink.object

            elif str(sink.predicate) == str(BITR4QS.branchIndex):
                revision.branch_index = sink.object

            elif str(sink.predicate) == str(BITR4QS.revisionNumber):
                revision.revision_number = sink.object

            cls._parse_valid_revision(revision, sink.predicate, sink.object)

        return revision, index

    @staticmethod
    def _get_transaction_revision(identifier):
        from src.main.bitr4qs.revision.TransactionRevision import TransactionRevision
        return TransactionRevision(URIRef(identifier))

    @staticmethod
    def _parse_transaction_revision(revision, p, o):
        predicates = [str(BITR4QS.branch), str(BITR4QS.snapshot), str(BITR4QS.tag), str(BITR4QS.update)]
        if str(p) in predicates:
            revision.add_valid_revision(o)

    @classmethod
    def parse_transaction_revision(cls, identifier, NTriples, index, revision=None):
        """
        Function that parses a general transaction revision
        :param identifier: The identifier of the transaction revision
        :param NTriples:
        :param index:
        :param revision:
        :return:
        """
        if revision is None:
            revision = cls._get_transaction_revision(identifier)

        sink = TripleSink()
        NTriplesParser = W3CNTriplesParser(sink=sink)

        for NTriple in NTriples:

            NTriplesParser.parsestring(NTriple)
            if identifier != str(sink.subject):
                return revision, index

            index += 1

            if str(sink.predicate) == str(BITR4QS.hash):
                revision.hexadecimal_of_hash = sink.object

            elif str(sink.predicate) == str(BITR4QS.precedingRevision):
                revision.preceding_revision = sink.object

            elif str(sink.predicate) == str(BITR4QS.revisionNumber):
                revision.revision_number = sink.object

            elif str(sink.predicate) == str(BITR4QS.branch):
                revision.branch = sink.object

            elif str(sink.predicate) == str(BITR4QS.createdAt):
                revision.creation_date = sink.object

            elif str(sink.predicate) == str(BITR4QS.author):
                revision.author = sink.object

            elif str(sink.predicate) == str(RDFS.comment):
                revision.description = sink.object

            cls._parse_transaction_revision(revision, sink.predicate, sink.object)

        return revision, index


class HeadParser(Parser):

    @staticmethod
    def _get_transaction_revision(identifier):
        from src.main.bitr4qs.revision.HeadRevision import HeadRevision
        return HeadRevision(URIRef(identifier))

    @staticmethod
    def _parse_transaction_revision(revision, p, o):
        pass