# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio Acquisition module."""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _

from .views.acquisition import blueprint as acquisition_blueprint

from .receivers.circulation import *
from .receivers.entity import *
from .receivers.user import *
from .receivers.record_action import *
from .receivers.lists import *
from .receivers.utils import *


class InvenioCirculationAcquisition(object):
    """Invenio-Circulation-Acquisition extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        # TODO: This is an example of translation string with comment. Please
        # remove it.
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.register_blueprint(acquisition_blueprint)
        app.extensions['invenio-circulation-acquisition'] = self

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            "CIRCULATION_ACQUISITION_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE",
                           "invenio_circulation_acquisition/base.html"))
