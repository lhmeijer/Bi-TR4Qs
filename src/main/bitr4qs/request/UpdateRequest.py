from .Request import Request
from src.main.bitr4qs.term.Triple import Triple
from rdflib.term import URIRef, Literal
from src.main.bitr4qs.term.Quad import Quad
from src.main.bitr4qs.term.Modification import Modification
from rdflib.namespace import XSD


class UpdateRequest(Request):

    def __init__(self, request):
        super().__init__(request)
        self._startDate = None
        self._endDate = None
        self._modifications = None

    @property
    def start_date(self) -> Literal:
        return self._startDate

    @start_date.setter
    def start_date(self, startDate: Literal):
        self._startDate = startDate

    @property
    def end_date(self) -> Literal:
        return self._endDate

    @end_date.setter
    def end_date(self, endDate: Literal):
        self._endDate = endDate

    @property
    def modifications(self):
        return self._modifications

    @modifications.setter
    def modifications(self, modifications):
        self._modifications = modifications


class UpdateQueryRequest(UpdateRequest):

    def __init__(self, updateQuery):
        super().__init__(updateQuery.request)
        self._updateQuery = updateQuery

    def _modifications_fom_query(self, revisionStore):
        self._modifications = []
        for update in self._updateQuery.translated_query:
            print("update ", update)
            if update.name == 'InsertData':
                node = self._evaluate_insert_or_delete_data(update, revisionStore)
                if node is not None:
                    return node
            elif update.name == 'DeleteData':
                node = self._evaluate_insert_or_delete_data(update, revisionStore, deletion=True)
                if node is not None:
                    return node
            else:
                pass
        return None

    def _can_quad_be_added_to_update(self, quad, revisionStore, deletion=False):
        canBeAdded = revisionStore.can_quad_be_added_or_deleted(
            quad, self._precedingTransactionRevision, self._revisionNumber, self._branch, self._startDate,
            self._endDate, deletion)
        return canBeAdded

    def _evaluate_insert_or_delete_data(self, update, revisionStore, deletion=False):
        """

        :param update:
        :param revisionStore:
        :param deletion:
        :return:
        """
        # Check whether a deleted or inserted triple can be added to the update
        for triple in update.triples:
            tripleNode = Triple(triple)
            if self._can_quad_be_added_to_update(tripleNode, revisionStore, deletion):
                self._modifications.append(Modification(tripleNode, deletion))
            else:
                return tripleNode

        for graph in update.quads:
            for triple in update.quads[graph]:
                quadNode = Quad(triple, graph)
                if self._can_quad_be_added_to_update(quadNode, revisionStore, deletion):
                    self._modifications.append(Modification(quadNode, deletion))
                else:
                    return quadNode
        return None

    def evaluate_request(self, revisionStore):
        super().evaluate_request(revisionStore)

        # Obtain start date
        startDate = self._request.values.get('startDate', None) or None
        if startDate is not None:
            self.start_date = Literal(str(startDate), datatype=XSD.dateTimeStamp)

        # Obtain end date
        endDate = self._request.values.get('endDate', None) or None
        if endDate is not None:
            self.end_date = Literal(str(endDate), datatype=XSD.dateTimeStamp)

        self._modifications_fom_query(revisionStore)


class ModifiedUpdateRequest(UpdateRequest):

    def __init__(self, request):
        super().__init__(request)
        self._precedingUpdateIdentifier = None
        self._precedingUpdates = None
        self._precedingUpdate = None

    def evaluate_request(self, revisionStore):
        super().evaluate_request(revisionStore)

        self._precedingUpdateIdentifier = self._request.view_args.get('updateID', None) or None
        self.preceding_valid_revision = self._precedingUpdateIdentifier
        self._precedingUpdates = revisionStore.preceding_update(self._precedingUpdateIdentifier)
        self._precedingUpdate = self._precedingUpdates[self._precedingUpdateIdentifier]

        # Obtain start date
        startDate = self._request.values.get('startDate', None) or None
        if startDate is not None:
            self.start_date = Literal(startDate, XSD.dateTimeStamp)
        else:
            self.start_date = self._precedingUpdate.start_date

        # Obtain end date
        endDate = self._request.values.get('endDate', None) or None
        if endDate is not None:
            self.end_date = Literal(endDate, XSD.dateTimeStamp)
        else:
            self.end_date = self._precedingUpdate.end_date


class ModifiedRepeatedUpdateRequest(ModifiedUpdateRequest):

    def evaluate_request(self, revisionStore):
        super().evaluate_request(revisionStore)

        # Obtain the modifications
        modifications = self._request.values.get('modifications', None) or None
        if modifications is None:   # Revert update
            self._modifications = []
        else:
            # modifications = []
            self._modifications = self._precedingUpdate.modifications
        # compare the modifications from the preceding update


class ModifiedRelatedUpdateRequest(ModifiedUpdateRequest):

    def evaluate_request(self, revisionStore):
        super().evaluate_request(revisionStore)

        # Obtain the modifications
        modifications = self._request.values.get('modifications', None) or None
        if modifications is None:  # Revert update
            self._modifications = []
            for precedingUpdate in self._precedingUpdates:
                for modification in precedingUpdate.modifications:
                    modification.invert()
                self._modifications.extend(precedingUpdate.modifications)
        else:
            # modifications = []
            self._modifications = []


