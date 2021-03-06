# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function, division

import warnings
import tempfile
import xml.etree.ElementTree as tree

import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons
from . import (IRSA_SERVER,
               GATOR_LIST_CATALOGS,
               ROW_LIMIT,
               TIMEOUT)


'''

API from

 http://irsa.ipac.caltech.edu/applications/Gator/GatorAid/irsa/catsearch.html

The URL of the IRSA catalog query service, CatQuery, is

 http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query

The service accepts the following keywords, which are analogous to the search
fields on the Gator search form:


spatial     Required    Type of spatial query: Cone, Box, Polygon, and NONE

polygon                 Convex polygon of ra dec pairs, separated by comma(,)
                        Required if spatial=polygon

radius                  Cone search radius
                        Optional if spatial=Cone, otherwise ignore it
                        (default 10 arcsec)

radunits                Units of a Cone search: arcsec, arcmin, deg.
                        Optional if spatial=Cone
                        (default='arcsec')

size                    Width of a box in arcsec
                        Required if spatial=Box.

objstr                  Target name or coordinate of the center of a spatial
                        search center. Target names must be resolved by
                        SIMBAD or NED.

                        Required only when spatial=Cone or spatial=Box.

                        Examples: 'M31'
                                  '00 42 44.3 -41 16 08'
                                  '00h42m44.3s -41d16m08s'

catalog     Required    Catalog name in the IRSA database management system.

outfmt      Optional    Defines query's output format.
                        6 - returns a program interface in XML
                        3 - returns a VO Table (XML)
                        2 - returns SVC message
                        1 - returns an ASCII table
                        0 - returns Gator Status Page in HTML (default)

desc        Optional    Short description of a specific catalog, which will
                        appear in the result page.

order       Optional    Results ordered by this column.

constraint  Optional    User defined query constraint(s)
                        Note: The constraint should follow SQL syntax.

onlist      Optional    1 - catalog is visible through Gator web interface
                        (default)

                        0 - catalog has been ingested into IRSA but not yet
                        visible through web interface.

                        This parameter will generally only be set to 0 when
                        users are supporting testing and evaluation of new
                        catalogs at IRSA's request.

If onlist=0, the following parameters are required:

    server              Symbolic DataBase Management Server (DBMS) name

    database            Name of Database.

    ddfile              The data dictionary file is used to get column
                        information for a specific catalog.

    selcols             Target column list with value separated by a comma(,)

                        The input list always overwrites default selections
                        defined by a data dictionary.

    outrows             Number of rows retrieved from database.

                        The retrieved row number outrows is always less than or
                        equal to available to be retrieved rows under the same
                        constraints.
'''

__all__ = ['Irsa']


class Irsa(BaseQuery):
    IRSA_URL = IRSA_SERVER()
    GATOR_LIST_URL = GATOR_LIST_CATALOGS()
    TIMEOUT = TIMEOUT()

    @class_or_instance
    def query_region(self, coordinates=None, catalog=None, spatial='Cone', radius=10 * u.arcsec,
                     width=None, polygon=None, get_query_payload=False, verbose=False):
        """
        This function can be used to perform either cone, box, polygon or all-sky
        search in the catalogs hosted by the NASA/IPAC Infrared Science Archive (IRSA).

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if
            performing a cone or box search. The string can give coordinates
            in various coordinate systems, or the name of a source that will
            be resolved on the server (see `here
            <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
            details). Required if spatial is 'Cone' or 'Box'. Optional if
            spatial is 'Polygon'.
        catalog : str
            The catalog to be used (see the *Notes* section below).
        spatial : str
            Type of spatial query: 'Cone', 'Box', 'Polygon', and 'All-Sky'.
            If missing then defaults to 'Cone'.
        radius : str or `astropy.units.Quantity` object, [optional for spatial is 'Cone']
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `astropy.units.Quantity` object [Required for spatial is 'Polygon'.]
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used.
        polygon : list, [Required for spatial is 'Polygon']
            A list of ``(ra, dec)`` pairs (as tuples), in decimal degrees,
            outlinining the polygon to search in. It can also be a list of
            `astropy.coordinates` object or strings that can be parsed by
            `astropy.coordinates.ICRSCoordinates`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            A table containing the results of the query
        """
        response = self.query_region_async(coordinates, catalog=catalog, spatial=spatial,
                                           radius=radius, width=width, polygon=polygon,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        return self._parse_result(response, verbose=verbose)

    @class_or_instance
    def query_region_async(self, coordinates=None, catalog=None,
                           spatial='Cone', radius=10 * u.arcsec, width=None,
                           polygon=None,get_query_payload=False):
        """
        This function serves the same purpose as :meth:`~astroquery.irsa.Irsa.query_region`,
        but returns the raw HTTP response rather than the results in an `astropy.table.Table`.

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if
            performing a cone or box search. The string can give coordinates
            in various coordinate systems, or the name of a source that will
            be resolved on the server (see `here
            <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
            details). Required if spatial is 'Cone' or 'Box'. Optional if
            spatial is 'Polygon'.
        catalog : str
            The catalog to be used (see the *Notes* section below).
        spatial : str
            Type of spatial query: 'Cone', 'Box', 'Polygon', and 'All-Sky'.
            If missing then defaults to 'Cone'.
        radius : str or `astropy.units.Quantity` object, [optional for spatial is 'Cone']
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `astropy.units.Quantity` object [Required for spatial is 'Polygon'.]
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used.
        polygon : list, [Required for spatial is 'Polygon']
            A list of ``(ra, dec)`` pairs (as tuples), in decimal degrees,
            outlinining the polygon to search in. It can also be a list of
            `astropy.coordinates` object or strings that can be parsed by
            `astropy.coordinates.ICRSCoordinates`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

         Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        if catalog is None:
            raise Exception("Catalog name is required!")

        request_payload = self._args_to_payload(catalog)
        request_payload.update(self._parse_spatial(spatial=spatial,
                                                   coordinates=coordinates,
                                                   radius=radius, width=width,
                                                   polygon=polygon))

        if get_query_payload:
            return request_payload
        response = commons.send_request(Irsa.IRSA_URL, request_payload,
                                        Irsa.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def _parse_spatial(self, spatial, coordinates, radius=None, width=None,
                       polygon=None):
        """
        Parse the spatial component of a query

        Parameters
        ----------
        spatial : str
            The type of spatial query. Must be one of: 'Cone', 'Box', 'Polygon', and 'All-Sky'.
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if
            performing a cone or box search. The string can give coordinates
            in various coordinate systems, or the name of a source that will
            be resolved on the server (see `here
            <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
            details). Required if spatial is 'Cone' or 'Box'. Optional if
            spatial is 'Polygon'.
        radius : str or `astropy.units.Quantity` object, [optional for spatial is 'Cone']
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `astropy.units.Quantity` object [Required for spatial is 'Polygon'.]
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used.
        polygon : list, [Required for spatial is 'Polygon']
            A list of ``(ra, dec)`` pairs as tuples of
            `astropy.coordinates.Angle`s outlinining the polygon to search in.
            It can also be a list of `astropy.coordinates` object or strings
            that can be parsed by `astropy.coordinates.ICRSCoordinates`.

        Returns
        -------
        Payload dictionary
        """

        request_payload = {}

        if spatial == 'All-Sky':
            spatial = 'NONE'
        elif spatial in ['Cone', 'Box']:
            if not _is_coordinate(coordinates):
                request_payload['objstr'] = coordinates
            else:
                request_payload['objstr'] = _parse_coordinates(coordinates)
            if spatial == 'Cone':
                radius = _parse_dimension(radius)
                request_payload['radius'] = radius.value
                request_payload['radunits'] = radius.unit.to_string()
            else:
                width = _parse_dimension(width)
                request_payload['size'] = width.to(u.arcsec).value
        elif spatial == 'Polygon':
            if coordinates is not None:
                request_payload['objstr'] = coordinates if not _is_coordinate(coordinates) else _parse_coordinates(coordinates)
            try:
                coordinates_list = [_parse_coordinates(c) for c in polygon]
            except (ValueError,TypeError):
                if isinstance(polygon[0], tuple):
                    try:
                        polygon = [(coord.Angle(pair[0]).degree, coord.Angle(pair[1]).degree) for pair in polygon]
                    except u.UnitsException:
                        warnings.warn("Polygon endpoints are being interpreted as RA/Dec pairs specified in decimal degree units.")
                    coordinates_list = [_format_decimal_coords(pair[0], pair[1]) for pair in polygon]
            request_payload['polygon'] = ','.join(coordinates_list)
        else:
            raise ValueError("Unrecognized spatial query type. " +
                             "Must be one of 'Cone', 'Box', 'Polygon', or 'All-Sky'.")

        request_payload['spatial'] = spatial

        return request_payload

    @class_or_instance
    def _args_to_payload(self, catalog):
        """
        Sets the common parameters for all cgi -queries

        Parameters
        ----------
        catalog : str
            The name of the catalog to query.

        Returns
        -------
        request_payload : dict
        """
        request_payload = dict(catalog=catalog,
                               outfmt=3,
                               outrows=ROW_LIMIT())
        return request_payload

    @class_or_instance
    def _parse_result(self, response, verbose=False):
        """
        Parses the results form the HTTP response to `astropy.table.Table`.

        Parameters
        ----------
        response : `requests.Response`
            The HTTP response object
        verbose : bool, optional
            Defaults to false. When true it will display warnings whenever the VOtable
            returned from the Service doesn't conform to the standard.

        Returns
        -------
        table : `astropy.table.Table`
        """
        if not verbose:
            commons.suppress_vo_warnings()
        # Check if results were returned
        if 'The catalog is not on the list' in response.content:
            raise Exception("Catalog not found")

        # Check that object name was not malformed
        if 'Either wrong or missing coordinate/object name' in response.content:
            raise Exception("Malformed coordinate/object name")

        # Check that the results are not of length zero
        if len(response.content) == 0:
            raise Exception("The IRSA server sent back an empty reply")

        # Write table to temporary file
        output = tempfile.NamedTemporaryFile()
        output.write(response.content)
        output.flush()

        # Read it in using the astropy VO table reader
        try:
            first_table = votable.parse(output.name, pedantic=False).get_first_table()
        except Exception as ex:
            print("Failed to parse votable! Returning raw result instead.")
            print(ex)
            return response.content

        # Convert to astropy.table.Table instance
        table = first_table.to_table()

        # Check if table is empty
        if len(table) == 0:
            warnings.warn("Query returned no results, so the table will be empty")

        return table

    @class_or_instance
    def list_catalogs(self):
        """
        Return a dictionary of the catalogs in the IRSA Gator tool.

        Returns
        -------
        catalogs : dict
            A dictionary of catalogs where the key indicates the catalog name to
            be used in query functions, and the value is the verbose description
            of the catalog.
        """
        response = commons.send_request(Irsa.GATOR_LIST_URL, dict(mode='xml'), Irsa.TIMEOUT, request_type="GET")
        root =tree.fromstring(response.content)
        catalogs = {}
        for catalog in root.findall('catalog'):
            catname = catalog.find('catname').text
            desc = catalog.find('desc').text
            catalogs[catname] = desc
        return catalogs

    @class_or_instance
    def print_catalogs(self):
        """
        Display a table of the catalogs in the IRSA Gator tool.
        """
        catalogs = self.list_catalogs()
        for catname in catalogs:
            print("{:30s}  {:s}".format(catname, catalogs[catname]))


def _is_coordinate(coordinates):
    try:
        coord.ICRSCoordinates(coordinates)
        return True
    except ValueError:
        return False


def _parse_coordinates(coordinates):
# borrowed from commons.parse_coordinates as from_name wasn't required in this case
    if isinstance(coordinates, basestring):
        try:
            c = coord.ICRSCoordinates(coordinates)
            warnings.warn("Coordinate string is being interpreted as an ICRS coordinate.")
        except u.UnitsException as ex:
            warnings.warn("Only ICRS coordinates can be entered as strings\n"
                          "For other systems please use the appropriate "
                          "astropy.coordinates object")
            raise ex
    elif isinstance(coordinates, coord.SphericalCoordinatesBase):
        c = coordinates
    else:
        raise TypeError("Argument cannot be parsed as a coordinate")
    formatted_coords = _format_decimal_coords(c.icrs.ra.degree, c.icrs.dec.degree)
    return formatted_coords


def _format_decimal_coords(ra, dec):
    """
    Print *decimal degree* RA/Dec values in an IPAC-parseable form
    """
    return '{0} {1:+}'.format(ra, dec)


def _parse_dimension(dim):
    if isinstance(dim, u.Quantity) and dim.unit in u.deg.find_equivalent_units():
        if dim.unit not in ['arcsec', 'arcmin', 'deg']:
            dim = dim.to(u.degree)
    # otherwise must be an Angle or be specified in hours...
    else:
        try:
            new_dim = commons.parse_radius(dim)
            dim = u.Quantity(new_dim.degree, u.Unit('degree'))
        except (u.UnitsException, coord.errors.UnitsError, AttributeError):
            raise u.UnitsException("Dimension not in proper units")
    return dim
