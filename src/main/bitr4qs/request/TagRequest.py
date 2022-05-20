from .Request import Request
from rdflib.term import URIRef, Literal
from rdflib.namespace import XSD
from src.main.bitr4qs.revision.Tag import Tag, TagRevision


class TagRequest(Request):

    type = 'tag'

    def __init__(self, request):
        super().__init__(request)

        self._effectiveDate = None
        self._transactionRevision = None
        self._tagName = None

    def evaluate_request(self, revisionStore):

        self.evaluate_request_to_modify(revisionStore)

        if self._effectiveDate is None:
            self._effectiveDate = self._creationDate

        # TODO throw error if not all variables have a value

    def evaluate_request_to_modify(self, revisionStore):
        super().evaluate_request(revisionStore)

        # Obtain the effective date
        effectiveDate = self._request.values.get('date', None) or None
        if effectiveDate is not None:
            self._effectiveDate = Literal(effectiveDate, datatype=XSD.dateTimeStamp)

        # Obtain the transaction time based on a given transaction revision
        revisionID = self._request.values.get('revision', None) or None
        if revisionID is not None:
            if revisionID == 'HEAD':
                self._transactionRevision = 'HEAD'
            else:
                revision = revisionStore.revision(revisionID=URIRef(revisionID), isValidRevision=False,
                                                  transactionRevisionA=self._precedingTransactionRevision)
                self._transactionRevision = revision.identifier

        # Obtain the name of the tag
        name = self._request.values.get('name', None) or None
        if name is not None:
            self._tagName = Literal(name)

    def transaction_revision_from_request(self):
        revision = TagRevision.revision_from_data(
            precedingRevision=self._precedingTransactionRevision, creationDate=self._creationDate, author=self._author,
            description=self._description, branch=self._branch, revisionNumber=self._revisionNumber)

        if self._transactionRevision == 'HEAD':
            self._transactionRevision = revision.identifier

        return revision

    def valid_revisions_from_request(self):
        print("self._tagName ", self._tagName)
        print("self._effectiveDate ", self._effectiveDate)
        print("self._transactionRevision ", self._transactionRevision)
        revision = Tag.revision_from_data(
            tagName=self._tagName, revisionNumber=self._revisionNumber, effectiveDate=self._effectiveDate,
            transactionRevision=self._transactionRevision, branchIndex=self._branchIndex)
        print("revision" , revision)
        return [revision]

    def modifications_from_request(self, revision, revisionStore):

        assert isinstance(revision, Tag), "Valid Revision should be a Tag"
        # AssertionError

        modifiedRevision = revision.modify(
            otherTagName=self._tagName, branchIndex=self._branchIndex, otherEffectiveDate=self._effectiveDate,
            otherTransactionRevision=self._transactionRevision, revisionNumber=self._revisionNumber,
            revisionStore=revisionStore)
        return [modifiedRevision]