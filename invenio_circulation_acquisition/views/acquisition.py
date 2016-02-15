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
import datetime

import invenio_circulation.models as circ_models
import invenio_circulation_acquisition.models as models
import invenio_circulation_acquisition.api as api

from flask import Blueprint, render_template, flash, request
from invenio_records.api import Record
from invenio_circulation.acl import circulation_admin_permission as cap

blueprint = Blueprint('acquisition', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


def _get_acquisition_data(user_id, record_id):
    rec = Record.get_record(record_id) if record_id else {}
    data = {'record_id': record_id, 'user_id': user_id}

    try:
        data['title'] = rec['title_statement']['title']
    except Exception:
        pass

    try:
        data['isbn'] = rec['international_standard_book_number']
    except Exception:
        pass

    imprint = 'publication_distribution_imprint'

    try:
        date = 'date_of_publication_distribution'
        data['year'] = rec[imprint][0][date][0]
    except Exception:
        pass

    try:
        publisher = 'name_of_publisher_distributor'
        data['publisher'] = rec[imprint][0][publisher][0]
    except Exception:
        pass

    data['authors'] = []
    pn = 'personal_name'
    try:
        data['authors'].append(rec['main_entry_personal_name'][pn])
    except Exception:
        pass

    try:
        tmp = [x[pn] for x in rec['added_entry_personal_name']]
        data['authors'].extend(tmp)
    except Exception:
        pass

    data['authors'] = '; '.join(data['authors'])


    return data


@blueprint.route('/acquisition/request_acquisition/<user_id>/')
@blueprint.route('/acquisition/request_acquisition/<user_id>/<record_id>')
def acquisition_request(user_id, record_id=0):
    data = _get_acquisition_data(user_id, record_id)
    return render_template('circulation_acquisition_request.html',
                           type='acquisition', delivery=True, action='request',
                           **data)


@blueprint.route('/acquisition/request_purchase/<user_id>/')
@blueprint.route('/acquisition/request_purchase/<user_id>/<record_id>')
def purchase_request(user_id, record_id=0):
    data = _get_acquisition_data(user_id, record_id)
    return render_template('circulation_acquisition_request.html',
                           type='purchase', delivery=True, action='request',
                           **data)


@blueprint.route('/acquisition/register_acquisition/')
@blueprint.route('/acquisition/register_acquisition/<record_id>')
@cap.require(403)
def acquisition_register(record_id=None):
    # data = _get_acquisition_data(user_id, record_id)
    data = {}
    return render_template('circulation_acquisition_register.html',
                           type='acquisition', action='register', **data)


@blueprint.route('/acquisition/register_purchase/')
@blueprint.route('/acquisition/register_purchase/<record_id>')
@cap.require(403)
def purchase_register(record_id=None):
    # data = _get_acquisition_data(user_id, record_id)
    data = {}
    return render_template('circulation_acquisition_register.html',
                           type='purchase', action='register', **data)


def _create_record(data):
    from copy import copy
    from invenio_records.api import create_record

    data = copy(data)
    del data['record_id']

    authors = data['authors'].split(';')
    if authors:
        main_author = authors[0]
        added_authors = authors[1:]

    record = {'title_statement': {'title': data['title']},
              'international_standard_book_number': data['isbn'],
              'publication_distribution_imprint': [
                  {'date_of_publication_distribution': [data['year']],
                   'name_of_publisher_distributor': [data['publisher']]}],
              'main_entry_personal_name': {'personal_name': main_author},
              'added_entry_personal_name': [
                  {'personal_name': x} for x in added_authors]}

    return create_record(record)


def _try_fetch_user(user):
    query_parts = []
    if user['ccid']:
        query_parts.append('ccid:{0}'.format(user['ccid']))
    if user['email']:
        query_parts.append('email:{0}'.format(user['email']))

    query = ' '.join(query_parts)

    return circ_models.CirculationUser.search(query)[0]


def _create_acquisition(data, user):
    if data['record']['record_id']:
        record = circ_models.CirculationRecord.get(data['record']['record_id'])
    else:
        # TODO: It might make sense to mark the new record as temporary
        record = _create_record(data['record'])
        record = circ_models.CirculationRecord.get(record['control_number'])

    acquisition_type = data['type']
    comments = data['comments']
    delivery = data.get('delivery')

    api.acquisition.request_acquisition(user, record, acquisition_type,
                                        comments, delivery)

    flash('Successfully created an acquisition request.')
    return ('', 200)


@blueprint.route('/api/acquisition/register_acquisition/', methods=['POST'])
@cap.require(403)
def register_acquisition():
    data = json.loads(request.get_json())
    user = _try_fetch_user(data['user'])
    return _create_acquisition(data, user)


@blueprint.route('/api/acquisition/request_acquisition/', methods=['POST'])
def request_acquisition():
    data = json.loads(request.get_json())
    user = circ_models.CirculationUser.get(data['user_id'])
    return _create_acquisition(data, user)


@blueprint.route('/api/acquisition/perform_action/', methods=['POST'])
def perform_acquisition_action():
    actions = {'confirm': api.acquisition.confirm_acquisition_request,
               'receive': api.acquisition.receive_acquisition,
               'deliver': api.acquisition.deliver_acquisition,
               'decline': api.acquisition.decline_acquisition_request,
               'cancel': api.acquisition.cancel_acquisition_request}
    msgs = {'confirm': 'confirmed', 'decline': 'declined',
            'receive': 'received', 'deliver': 'delivered',
            'cancel': 'canceled'}

    data = json.loads(request.get_json())
    action = data['action']
    acquisition_clc_id = data['acquisition_clc_id']

    acquisition_clc = models.AcquisitionLoanCycle.get(acquisition_clc_id)

    actions[action](acquisition_clc)

    msg = 'Successfully {0} the acquisition request {1}.'
    msg = msg.format(msgs[action], acquisition_clc_id)
    flash(msg)
    return ('', 200)
