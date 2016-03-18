/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it wacquisition be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

define(
    [
        'jquery',
        'node_modules/bootstrap-datepicker/js/bootstrap-datepicker',
    ],
function($, _bdp) {
    $('#entity_detail').ready(function() {
        if ($('#entity_detail').length == 0) {
            return;
        }
        var editor = $('#entity_detail');
        var data = JSON.parse(editor.attr('data-editor_data'));
        var schema = JSON.parse(editor.attr('data-editor_schema'));

        json_editor = new JSONEditor($('#entity_detail')[0], 
                {
                    schema: schema,
                    theme: 'bootstrap3',
                    no_additional_properties: true,
                });
        json_editor.setValue(data);
    });

    $('#acquisition_request_submit').on('click', function(){
        // Get record values
        var rec = {};
        $('#acquisition_document').find('.form-control').each(function(index, element) {
            rec[$(element).data('value_name')] = element.value;
        });

        // Get user values
        var user = {};
        $('#user_form').find('.form-control').each(function(index, element) {
            user[$(element).data('value_name')] = element.value;
        });

        var record_id = $('#acquisition_document').data('record_id');
        var acquisition_type = $(this).data('type');
        var delivery = $('#circulation_option_delivery').val();
        var payment_method = $('#circulation_option_payment_method').val();
        var budget_code = $('#circulation_option_budget_code').val();
        var copies = $('#circulation_option_copies').val();
        var comments = $('#circulation_option_comments').val();

        if ($(this).data('action') == 'request'){
            var url = '/circulation/api/acquisition/request_acquisition/';
        } else {
            var url = '/circulation/api/acquisition/register_acquisition/';
        }
        var data = {record: rec, user: user, record_id: record_id, 
                    acquisition_type: acquisition_type,
                    payment_method: payment_method, budget_code: budget_code,
                    comments: comments, delivery: delivery, copies: copies};

        function success() {
            $(document).scrollTop(0);
            window.location.reload();
        }

        $.ajax({
            type: "POST",
            url: url,
            data: JSON.stringify(JSON.stringify(data)),
            success: success,
            contentType: 'application/json',
        });
    });

    $('#circulation_option_payment_method').on('change', function(event) {
        if (event.target.value == 'Budget Code') {
            $('#circulation_option_budget_code').show();
        } else {
            $('#circulation_option_budget_code').hide();
        }
    });
});
