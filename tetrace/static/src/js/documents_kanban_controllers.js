odoo.define('tetrace.DocumentsKanbanControllerTetrace', function (require) {
"use strict";

var DocumentsKC = require('documents.DocumentsKanbanController');

//var Chatter = require('mail.Chatter');

var core = require('web.core');
var session = require('web.session');
var utils = require('web.utils');
var KanbanController = require('web.KanbanController');

var qweb = core.qweb;
var _t = core._t;

console.log("rrrrrrrrrrrrrr");

DocumentsKC.include({
    async _processFiles(files, documentID) {
        console.log("dddddddddddddddddddd");
        const uploadID = _.uniqueId('uploadID');
        const folderID = this._searchPanel.getSelectedFolderId();
        const context = this.model.get(this.handle, { raw: true }).getContext();

        if (!folderID && !documentID) { return; }
        if (!files.length) { return; }

        const data = new FormData();

        data.append('csrf_token', core.csrf_token);
        data.append('folder_id', folderID);
        if (documentID) {
            if (files.length > 1) {
                // preemptive return as it doesn't make sense to upload multiple files inside one document.
                return;
            }
            data.append('document_id', documentID);
        }
        console.log(context);
        if (context) {
            if (context.default_partner_id) {
                data.append('partner_id', context.default_partner_id);
            }
            if (context.default_owner_id) {
                data.append('owner_id', context.default_owner_id);
            }
            if (context.params && context.params.model == 'hr.employee' && context.params.id != undefined) {
                data.append('res_model', context.params.model);
                data.append('res_id', context.params.id);
            }
        }
        for (const file of files) {
            data.append('ufile', file);
        }
        let title = files.length + ' Files';
        let type;
        if (files.length === 1) {
            title = files[0].name;
            type = files[0].type;
        }
        console.log(data);
        const prom = new Promise(resolve => {
            const xhr = this._createXHR();
            xhr.open('POST', '/documents/upload_attachment');
            if (documentID) {
                this._makeReplaceProgress(uploadID, documentID, xhr);
            } else {
                this._makeNewProgress(uploadID, folderID, xhr, title, type);
            }
            const progressPromise = this._attachProgressBars();
            xhr.onload = async () => {
                await progressPromise;
                resolve();
                let result = {error: xhr.status};
                if (xhr.status === 200) {
                    result = JSON.parse(xhr.response);
                }
                if (result.error) {
                    this.do_notify(_t("Error"), result.error, true);
                }
                this._removeProgressBar(uploadID);
            };
            xhr.onerror = async () => {
                await progressPromise;
                resolve();
                this.do_notify(xhr.status, _.str.sprintf(_t('message: %s'), xhr.reponseText), true);
                this._removeProgressBar(uploadID);
            };
            xhr.send(data);
        });
        return prom;
    },
});

return DocumentsKC;
});
