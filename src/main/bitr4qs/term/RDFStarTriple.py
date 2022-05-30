from rdflib.term import URIRef, Literal
from .Triple import Triple


class RDFStarTriple(object):

    def __init__(self, value):
        s, p, o = value

        self.subject = s
        self.predicate = p
        self.object = o

    @property
    def subject(self):
        return self._subject

    @subject.setter
    def subject(self, subject):
        assert isinstance(subject, URIRef) or isinstance(subject, Triple)
        self._subject = subject

    @property
    def predicate(self):
        return self._predicate

    @predicate.setter
    def predicate(self, predicate):
        assert isinstance(predicate, URIRef)
        self._predicate = predicate

    @property
    def object(self):
        return self._object

    @object.setter
    def object(self, newObject):
        assert isinstance(newObject, URIRef) or isinstance(newObject, Triple)
        self._object = newObject

    def triple(self):
        return self._subject, self._predicate, self._object

    def sparql(self):
        return ' '.join(self.represent_term(term) for term in self.triple()) + ' .'

    def n_quad(self):
        return ' '.join(self.represent_term(term) for term in self.triple()) + ' .\n'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.represent_term(self._subject) != self.represent_term(other.subject):
                return False
            if self.represent_term(self._predicate) != self.represent_term(other.predicate):
                return False
            if self.represent_term(self._object) != self.represent_term(other.object):
                return False
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '({0})'.format(','.join(self.represent_term(term) for term in self.triple()))

    def represent_term(self, term):
        if isinstance(term, Literal):
            return self._quote_literal(term)
        elif isinstance(term, Triple):
            return term.rdf_star()
        else:
            return term.n3()

    def _quote_literal(self, l_):
        """
        a simpler version of term.Literal.n3()
        """

        encoded = self._quote_encode(l_)

        if l_.language:
            if l_.datatype:
                raise Exception("Literal has datatype AND language!")
            return "%s@%s" % (encoded, l_.language)
        elif l_.datatype:
            return "%s^^<%s>" % (encoded, l_.datatype)
        else:
            return "%s" % encoded

    @staticmethod
    def _quote_encode(l_):
        return '"%s"' % l_.replace("\\", "\\\\").replace("\n", "\\n").replace(
            '"', '\\"').replace("\r", "\\r")


