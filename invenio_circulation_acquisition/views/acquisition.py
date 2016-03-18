# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it wacquisition be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import json

import invenio_circulation.models as circ_models
import invenio_circulation_acquisition.api as api

from flask import Blueprint, render_template, flash, request
from flask_login import current_user
from invenio_records.api import Record
from invenio_circulation.acl import circulation_admin_permission as cap
from invenio_circulation.views.utils import get_user

blueprint = Blueprint('acquisition', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')

rec_fields = [(('title_statement', 'title'), ''),
              (('international_standard_book_number',
                'international_standard_book_number'), ''),
              (('publication_distribution_imprint', 0,
                'date_of_publication_distribution', 0), ''),
              (('publication_distribution_imprint', 0,
                'name_of_publisher_distributor', 0), ''),
              (('international_standard_serial_number',
                'international_standard_serial_number'), ''),
              (('edition_statement', 'edition_statement'), ''),
              (('host_item_entry', 'abbreviated_title'), ''),
              (('host_item_entry', 'volume'), ''),
              (('host_item_entry', 'issue'), ''),
              (('host_item_entry', 'pages'), ''),
              (('host_item_entry', 'year'), '')]


def _prepare_record(record, fields):
    def _get_struct(field, index, value):
        try:
            return [] if type(field[index+1]) == int else {}
        except IndexError:
            return value

    for field, value in fields:
        rec = record

        for i, key in list(enumerate(field)):
            if isinstance(rec, dict):
                if key not in rec:
                    rec[key] = _get_struct(field, i, value)
                rec = rec[key]
            elif isinstance(rec, list):
                if key >= len(rec):
                    rec.append(_get_struct(field, i, value))
                rec = rec[key]


def _prepare_record_authors(rec):
    key = 'circulation_compact_authors'
    rec[key] = []
    pn = 'personal_name'

    try:
        rec[key].append(rec['main_entry_personal_name'][pn])
    except Exception:
        pass

    try:
        rec[key].extend([x[pn] for x in rec['added_entry_personal_name']])
    except Exception:
        pass

    rec[key] = '; '.join(rec[key])


@blueprint.route('/acquisition/request_acquisition/')
@blueprint.route('/acquisition/request_acquisition/<record_id>')
def acquisition_request(record_id=None):
    try:
        get_user(current_user)
    except AttributeError:
        # Anonymous User
        return render_template('invenio_theme/401.html')

    rec = Record.get_record(record_id) if record_id else {}
    _prepare_record(rec, rec_fields)
    _prepare_record_authors(rec)

    return render_template('circulation_acquisition_request.html',
                           type='acquisition', action='request',
                           **rec)


@blueprint.route('/acquisition/request_purchase/')
@blueprint.route('/acquisition/request_purchase/<record_id>')
def purchase_request(record_id=0):
    try:
        get_user(current_user)
    except AttributeError:
        # Anonymous User
        return render_template('invenio_theme/401.html')

    rec = Record.get_record(record_id) if record_id else {}
    _prepare_record(rec, rec_fields)
    _prepare_record_authors(rec)

    return render_template('circulation_acquisition_request.html',
                           type='purchase', delivery=True, action='request',
                           **rec)


@blueprint.route('/acquisition/register_acquisition/')
@blueprint.route('/acquisition/register_acquisition/<record_id>')
@cap.require(403)
def acquisition_register(record_id=None):
    rec = Record.get_record(record_id) if record_id else {}
    _prepare_record(rec, rec_fields)
    _prepare_record_authors(rec)
    return render_template('circulation_acquisition_request.html',
                           type='acquisition', action='register', **rec)


@blueprint.route('/acquisition/register_purchase/')
@blueprint.route('/acquisition/register_purchase/<record_id>')
@cap.require(403)
def purchase_register(record_id=None):
    rec = Record.get_record(record_id) if record_id else {}
    _prepare_record(rec, rec_fields)
    _prepare_record_authors(rec)
    return render_template('circulation_acquisition_register.html',
                           type='purchase', delivery=True, action='register',
                           **rec)


def _create_record(data):
    # TODO: It might make sense to mark the new record as temporary
    import uuid
    import dateutil.parser as parser

    from invenio_db import db
    from invenio_pidstore.minters import recid_minter
    from invenio_indexer.api import RecordIndexer
    from invenio_records.api import Record

    def _get_keys(key_string):
        return [int(x) if x.isdigit() else unicode(x)
                for x in key_string.split('.')]

    authors = data['circulation_compact_authors'].split(';')
    del data['circulation_compact_authors']

    fields = [(_get_keys(key), unicode(value)) for key, value in data.items()]

    rec = {}
    _prepare_record(rec, fields)

    rec[u'main_entry_personal_name'] = {u'personal_name': unicode(authors[0])}
    rec[u'added_entry_personal_name'] = [{u'personal_name': unicode(x)}
                                         for x in authors[1:]]

    # We need to check the year here
    year = (rec[u'publication_distribution_imprint'][0]
               [u'date_of_publication_distribution'][0])

    if year == u'':
        del (rec[u'publication_distribution_imprint'][0]
                [u'date_of_publication_distribution'])

    parser.parse(year)

    rec_uuid = uuid.uuid4()
    pid = recid_minter(rec_uuid, rec)
    rec[u'recid'] = int(pid.pid_value)
    rec[u'uuid'] = unicode(str(rec_uuid))

    r = Record.create(rec, id_=rec_uuid)
    RecordIndexer().index(r)

    db.session.commit()

    return r


def _try_fetch_user(user):
    query_parts = []
    if user['ccid']:
        query_parts.append('ccid:{0}'.format(user['ccid']))
    if user['email']:
        query_parts.append('email:{0}'.format(user['email']))

    query = ' '.join(query_parts)

    return circ_models.CirculationUser.search(query)[0]


def _create_acquisition(data, user):
    try:
        record = circ_models.CirculationRecord.get(data['record_id'])
    except Exception:
        try:
            record = _create_record(data['record'])
        except ValueError:
            return ('', 500)
        record = circ_models.CirculationRecord.get(record['uuid'])

    acquisition_type = data['acquisition_type']
    comments = data['comments']
    delivery = data['delivery']
    payment_method = data['payment_method']
    budget_code = data['budget_code']
    copies = int(data['copies'])

    api.acquisition.request_acquisition(user, record, acquisition_type,
                                        copies, payment_method, budget_code,
                                        delivery, comments)

    flash('Successfully created an {0} request.'.format(acquisition_type))
    return ('', 200)


@blueprint.route('/api/acquisition/register_acquisition/', methods=['POST'])
@cap.require(403)
def register_acquisition():
    data = json.loads(request.get_json())
    user = _try_fetch_user(data['user'])
    return _create_acquisition(data, user)


@blueprint.route('/api/acquisition/request_acquisition/', methods=['POST'])
def request_acquisition():
    try:
        user = get_user(current_user)
        data = json.loads(request.get_json())
        return _create_acquisition(data, user)
    except AttributeError:
        return ('', 403)
