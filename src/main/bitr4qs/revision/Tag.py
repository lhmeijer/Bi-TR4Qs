from .Revision import Revision
from rdflib.term import URIRef, Literal
from src.main.bitr4qs.term.Triple import Triple
from src.main.bitr4qs.namespace import BITR4QS


class Tag(Revision):

    typeOfRevision = BITR4QS.Tag
    nameOfRevision = 'Tag'

    def __init__(self, identifier: URIRef = None,
                 precedingRevision: URIRef = None,
                 hexadecimalOfHash: Literal = None,
                 tagName: Literal = None,
                 effectiveDate: Literal = None,
                 transactionRevision: URIRef = None):
        super().__init__(identifier, precedingRevision, hexadecimalOfHash)
        self.tag_name = tagName
        self.effective_date = effectiveDate
        self.transaction_revision = transactionRevision

    @property
    def tag_name(self):
        return self._tagName

    @tag_name.setter
    def tag_name(self, tagName: Literal):
        if tagName is not None:
            self._RDFPatterns.append(Triple((self._identifier, BITR4QS.tagName, tagName)))
        self._tagName = tagName

    @property
    def effective_date(self):
        return self._effectiveDate

    @effective_date.setter
    def effective_date(self, effectiveDate: Literal):
        if effectiveDate is not None:
            self._RDFPatterns.append(Triple((self._identifier, BITR4QS.validAt, effectiveDate)))
        self._effectiveDate = effectiveDate

    @property
    def transaction_revision(self):
        return self._transactionRevision

    @transaction_revision.setter
    def transaction_revision(self, transactionRevision: URIRef):
        if transactionRevision is not None:
            self._RDFPatterns.append(Triple((self._identifier, BITR4QS.transactedAt, transactionRevision)))
        self._transactionRevision = transactionRevision

    @classmethod
    def _revision_from_request(cls, request):
        return cls(tagName=request.tag_name, effectiveDate=request.effective_date, transactionRevision=request.transaction_revision,
                   precedingRevision=request.preceding_revision)
