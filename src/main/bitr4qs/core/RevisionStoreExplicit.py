from .RevisionStore import RevisionStore
from rdflib.term import Literal, URIRef
import src.main.bitr4qs.tools.parser as parser
from src.main.bitr4qs.namespace import BITR4QS


class RevisionStoreExplicit(RevisionStore):

    def get_modifications_of_updates_between_revisions(self, revisionA, revisionB, date, updateParser, quadPattern,
                                                       forward=True):
        updateSucceedingTimeString = self._update_time_string(date=date, variableName='?succeedingUpdate')
        construct, where = self._construct_where_for_update(quadPattern=quadPattern)
        if self.config.related_update_content():
            updatePrecedingTimeString = self._update_time_string(date=date, variableName='?succeedingUpdate')
            SPARQLQuery = """PREFIX : <{0}>
            CONSTRUCT {{ {1} }}
            WHERE {{
                    {{
                    SELECT ?precedingUpdate
                    WHERE {{
                         {2} :precedingRevision* ?revision .
                         ?revision :precedingRevision+ {3} .
                         ?revision :update ?succeedingUpdate .{4}
                         ?succeedingUpdate :precedingUpdate ?precedingUpdate .
                        }}
                    }}
                {3} :precedingRevision* ?revision .
                ?revision :update ?precedingUpdate .{5}
                ?precedingUpdate :precedingUpdate* ?update .
                {6} }}""".format(str(BITR4QS), construct, revisionA.n3(), revisionB.n3(), updateSucceedingTimeString,
                                 updatePrecedingTimeString, where)
        else:
            updateTimeString = self._update_time_string(date=date, variableName='?update')
            SPARQLQuery = """PREFIX : <{0}>
            CONSTRUCT {{ {1} }}
            WHERE {{
                    {{
                    SELECT ?update
                    WHERE {{
                         {2} :precedingRevision* ?revision .
                         ?revision :precedingRevision+ {3} .
                         ?revision :update ?succeedingUpdate .{4}
                         ?succeedingUpdate :precedingUpdate ?update .
                        }}
                    }}
                {3} :precedingRevision* ?revision .
                ?revision :update ?update .{5}
                {6} }}""".format(str(BITR4QS), construct, revisionA.n3(), revisionB.n3(), updateSucceedingTimeString,
                                 updateTimeString, where)

        print('SPARQLQuery ', SPARQLQuery)
        stringOfUpdates = self._revisionStore.execute_construct_query(SPARQLQuery, 'nquads')
        print("stringOfUpdates ", stringOfUpdates)
        updateParser.parse_aggregate(stringOfUpdates, forward)

    def _tag_revisions_in_revision_graph(self, revisionA: URIRef, revisionB: URIRef = None):
        """

        :param revisionA:
        :param revisionB:
        :return:
        """
        revisionEndConstrain = ""
        if revisionB is not None:
            revisionEndConstrain = "\n?revision :precedingRevision+ {0} .".format(revisionB.n3())

        SPARQLQuery = """PREFIX : <{0}>
        CONSTRUCT {{ ?revision :precedingRevision ?precedingRevision . 
        ?revision :tag ?tag . }}
        WHERE {{ {1} :precedingRevision* ?revision .{2}
        ?revision :precedingRevision ?precedingRevision .
        ?revision :tag ?tag . 
        }}""".format(str(BITR4QS), revisionA.n3(), revisionEndConstrain)
        stringOfTagRevisions = self._revisionStore.execute_construct_query(SPARQLQuery, 'nquads')
        return stringOfTagRevisions

    def tags_in_revision_graph(self, revisionA: URIRef, revisionB: URIRef = None):
        """

        :param revisionA:
        :param revisionB:
        :return:
        """
        tags = self._valid_revisions_in_graph(revisionA=revisionA, validRevisionType='Tag', revisionB=revisionB,
                                              queryType='DescribeQuery')
        tagRevisions = self._tag_revisions_in_revision_graph(revisionA, revisionB)
        tags = parser.TagParser.parse_sorted_explicit(tags, tagRevisions, endRevision=revisionA)
        return tags

    def is_transaction_time_a_earlier(self, revisionA, revisionB) -> bool:
        """

        :param revisionA:
        :param revisionB:
        :return:
        """
        SPARQLString = """PREFIX : <{0}>
        ASK {{ {1} :precedingRevision+ {2} }}
        """.format(str(BITR4QS), revisionB.n3(), revisionA.n3())
        result = self._revisionStore.execute_ask_query(SPARQLString)
        return result

    def _transaction_revision(self, transactionRevisionA, transactionRevision, transactionRevisionB=None):
        earlyStop = ""
        if transactionRevisionB is not None:
            earlyStop = "\n?revision :precedingRevision+ {0} .".format(transactionRevisionB.n3())

        SPARQLQuery = """PREFIX : <{0}>
        DESCRIBE ?revision
        {{ {1} :precedingRevision* ?revision .{2}
        FILTER ( {3} = ?revision ) }}""".format(str(BITR4QS), transactionRevisionA.n3(), earlyStop,
                                                transactionRevision.n3())
        return SPARQLQuery

    def _valid_revisions_in_graph(self, revisionA: URIRef, revisionType: str, queryType: str,
                                  revisionB: URIRef = None, prefix=True, timeConstrain=""):
        """

        :param revisionA:
        :param validRevisionType:
        :param revisionB:
        :return:
        """
        earlyStopA = earlyStopB = ""
        if revisionB is not None:
            earlyStopA = "\n?revision :precedingRevision+ {0} .".format(revisionB.n3())
            earlyStopB = "\n?otherRevision :precedingRevision+ {0} .".format(revisionB.n3())

        queryString = "DESCRIBE" if queryType == 'DescribeQuery' else 'SELECT'
        prefixString = "PREFIX : <{0}>".format(str(BITR4QS)) if prefix else ""

        SPARQLQuery = """{0}
        {6} ?{1}
        WHERE {{ {2} :precedingRevision* ?revision .{3}
            ?revision :{1} ?{1} .{7}
            MINUS {{
                {2} :precedingRevision* ?otherRevision .{4}
                ?otherRevision :{1} ?other .
                ?other :preceding{5} ?{1} . 
            }}
        }}""".format(prefixString, revisionType, revisionA.n3(), earlyStopA, earlyStopB, revisionType.title(),
                     queryString, timeConstrain)

        if prefix and queryType == 'DescribeQuery':
            stringOfValidRevisions = self._revisionStore.execute_describe_query(SPARQLQuery, 'nquads')
            return stringOfValidRevisions
        else:
            return SPARQLQuery

    def _valid_revisions_from_transaction_revision(self, transactionRevisionID, revisionType):
        if revisionType == 'update':
            where = "{0} :update ?revision .".format(transactionRevisionID.n3())
        elif revisionType == 'snapshot':
            where = "{0} :snapshot ?revision .".format(transactionRevisionID.n3())
        elif revisionType == 'tag':
            where = "{0} :tag ?revision .".format(transactionRevisionID.n3())
        elif revisionType == 'branch':
            where = "{0} :branch ?revision .\nOPTIONAL {{ {0} :update ?revision }}".format(transactionRevisionID.n3())
        elif revisionType == 'revert':
            where = """
            {0} :revert ?revision .
            OPTIONAL {{ {0} :update ?revision }}
            OPTIONAL {{ {0} :tag ?revision }}
            OPTIONAL {{ {0} :snapshot ?revision }}
            OPTIONAL {{ {0} :branch ?revision }}""".format(transactionRevisionID.n3())
        else:
            where = ""

        SPARQLQuery = """PREFIX : <{0}>
        DESCRIBE ?revision
        WHERE {{ {1} }} 
        }}""".format(str(BITR4QS), where)
        return SPARQLQuery

