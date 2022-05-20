from .Query import Query
from rdflib.term import URIRef, Literal
from src.main.bitr4qs.core.Version import Version
from rdflib.namespace import XSD
from src.main.bitr4qs.tools.parser.UpdateParser import UpdateParser


class DMQuery(Query):

    def __init__(self, request, base=None):
        super().__init__(request, base)

        self._transactionTimeA = None
        self._validTimeA = None

        self._transactionTimeB = None
        self._validTimeB = None

    @property
    def transaction_time_a(self) -> URIRef:
        return self._transactionTimeA

    @transaction_time_a.setter
    def transaction_time_a(self, transactionTimeA: URIRef):
        self._transactionTimeA = transactionTimeA

    @property
    def transaction_time_b(self) -> URIRef:
        return self._transactionTimeB

    @transaction_time_b.setter
    def transaction_time_b(self, transactionTimeB: URIRef):
        self._transactionTimeB = transactionTimeB

    @property
    def valid_time_a(self) -> Literal:
        return self._validTimeA

    @valid_time_a.setter
    def valid_time_a(self, validTimeA: Literal):
        self._validTimeA = validTimeA

    @property
    def valid_time_b(self) -> Literal:
        return self._validTimeB

    @valid_time_b.setter
    def valid_time_b(self, validTimeB: Literal):
        self._validTimeB = validTimeB

    def evaluate_query(self, revisionStore):
        super().evaluate_query(revisionStore)

        tagNameA = self._request.values.get('tagA', None) or None
        if tagNameA is not None:
            try:
                tagA = revisionStore.tag_from_name(Literal(tagNameA))
                self._transactionTimeA = tagA.transaction_revision
                self._validTimeA = tagA.effective_date
            except Exception as e:
                raise e
            # TODO Tag does not exist

        tagNameB = self._request.values.get('tagB', None) or None
        if tagNameB is not None:
            try:
                tagB = revisionStore.tag_from_name(Literal(tagNameA))
                self._transactionTimeB = tagB.transaction_revision
                self._validTimeB = tagB.effective_date
            except Exception as e:
                raise e
            # TODO Tag does not exist

        revisionIDB = self._request.view_args.get('revisionB', None) or None
        # TODO RevisionB does not exist or is not given.
        if revisionIDB is not None:
            self._transactionTimeB = URIRef(revisionIDB)

        revisionIDA = self._request.view_args.get('revisionA', None) or None
        # TODO RevisionA does not exist or is not given.
        if revisionIDA is not None:
            try:
                revisionA = revisionStore.revision(revisionID=URIRef(revisionIDA), isValidRevision=False,
                                                   transactionRevisionA=self._transactionTimeB)
                self._transactionTimeA = revisionA.identifier
            except Exception as e:
                raise e

        validDateA = self._request.view_args.get('dateA', None) or None
        # TODO no valid date A is given.
        if validDateA is not None:
            self._validTimeA = Literal(validDateA, datatype=XSD.dateTimeStamp)

        validDateB = self._request.view_args.get('dateB', None) or None
        # TODO no valid date B is given.
        if validDateB is not None:
            self._validTimeB = Literal(validDateB, datatype=XSD.dateTimeStamp)

    def apply_query(self, revisionStore):
        updateParser = UpdateParser()
        Version.modifications_between_two_states(transactionA=self._transactionTimeA, validA=self._validTimeA,
                                                 transactionB=self._transactionTimeB, validB=self._validTimeB,
                                                 revisionStore=revisionStore, updateParser=updateParser,
                                                 quadPattern=self._quadPattern)
        modifications = updateParser.get_list_of_modifications()

        # TODO check which queryType -> return a result for each queryType
        if self._queryType == 'SelectQuery':
            return self._apply_select_query(modifications)
        elif self._queryType == 'ConstructQuery':
            pass
        elif self._queryType == 'AskQuery':
            pass
        elif self._queryType == 'DescribeQuery':
            pass
        else:
            pass

    def _apply_select_query(self, modifications):
        # Check the variables in the SPARQL query, and returns these and separate them based on insertions and deletions
        variables = self._quadPattern.get_variables()
        results = {'head': {'vars': [var for var, _ in variables]}, 'result': {'insertions': [], 'deletions': []}}
        for modification in modifications:
            result = {}
            for variable, index in variables:
                if index == 0:
                    value = modification.value.subject
                elif index == 1:
                    value = modification.value.predicate
                elif index == 2:
                    value = modification.value.object
                else:
                    value = modification.value.graph

                if isinstance(value, URIRef):
                    result[variable] = {'type': 'uri', 'value': str(value)}
                elif isinstance(value, Literal):
                    result[variable] = {'type': 'literal', 'value': str(value)}

            if modification.deletion:
                results['result']['deletions'].append(result)
            else:
                results['result']['insertions'].append(result)

        return results
