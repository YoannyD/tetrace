odoo.define('registro_tiempo.form', function (require) {
"use strict";

require('web_editor.ready');
//DevExpress.localization.locale(navigator.language || navigator.browserLanguage);
//DevExpress.ui.dxOverlay.baseZIndex(2000);
//Globalize.loadMessages({'es': es});

var base = require('web_editor.base');
var ajax = require('web.ajax');

base.ready().then(function () {
    var current_position;
    var mapWidget;
    initGeolocation();
    function initGeolocation(){
        if( navigator.geolocation ){
            // Call getCurrentPosition with success and failure callbacks
            navigator.geolocation.getCurrentPosition(get_position, function(){});
        }else{
            alert("Sorry, your browser does not support geolocation services.");
        }
    }

    function get_position(position){
        current_position = position;
        console.log(current_position);
        console.log(mapWidget);
        console.log([{ lat: current_position.coords.latitude, lng: current_position.coords.longitude}]);
        mapWidget.option("markers", [{
            location: { lat: current_position.coords.latitude, lng: current_position.coords.longitude},
            tooltip: {
                text: "Tú ubicación"
            }
        }]);
        mapWidget.option("center", { lat: current_position.coords.latitude, lng: current_position.coords.longitude});
    }

    if($("#project_search").length){
        var projectDataSource = new DevExpress.data.CustomStore({
            key: "id",
            load: function(loadOptions) {
                var params = {
                    "offset": loadOptions.skip,
                    "limit": loadOptions.take,
                }

                if(loadOptions.searchValue){
                    params["search"] = loadOptions.searchValue;
                }

                return sendRequest("/api/projects", params);
            },
        });

        var project_search = $("#project_search").dxSelectBox({
            dataSource: projectDataSource,
            displayExpr: "name",
            valueExpr: "id",
            searchEnabled: true
        }).dxSelectBox("instance");
    }

    if($("#map_registro_horas").length){
        var location = {};
        if(current_position){
            location = { lat: current_position.coords.latitude, lng: current_position.coords.longitude};
        }
        mapWidget = $("#map_registro_horas").dxMap({
            provider: "bing",
            zoom: 11,
            height: 200,
            width: "100%",
            controls: true,
            markers: [{
                location: location,
                tooltip: {
                    text: "Tú ubicación"
                }
            }]
        }).dxMap("instance");

    }

    $("#icon-play").dxButton({
        icon: "fa fa-play-circle",
        type: "success",
        onClick: function(e) {
            var project_id = $("#project_search").dxSelectBox("instance").option('value');
            if(!project_id){
                DevExpress.ui.notify("Tiene que elegir un proyecto.", "error");
                return;
            }
            var params = {
                'project_id': project_id
            }
            iniciar_tiempo(params);
        }
    });

    $("#icon-stop").dxButton({
        icon: "fa fa-stop-circle",
        type: "danger",
        onClick: function(e) {
            var project_id = $("#project_search").dxSelectBox("instance").option('value');
            if(!project_id){
                DevExpress.ui.notify("Tiene que elegir un proyecto.", "error");
                return;
            }
            var params = {
                'project_id': project_id
            }
            parar_tiempo(params);
        }
    });

    if($("#form-registro-horas").length){
        var formWidget = $("#form-registro-horas").dxForm({
//            formData: formData,
            readOnly: false,
            showColonAfterLabel: true,
            minColWidth: 300,
            showValidationSummary: true,
            items:[
                {
                    dataField: "project_id",
                    label: {
                        text: "Proyecto"
                    },
                    editorType: "dxSelectBox",
                    editorOptions: {
                        dataSource: projectDataSource,
                        displayExpr: "name",
                        valueExpr: "id",
                        searchEnabled: true
                    },
                    validationRules: [{ type: "required" }]
                },
                {
                    dataField: "fecha",
                    label: {
                        text: "Fecha"
                    },
                    editorType: "dxDateBox",
                    editorOptions: {
                        displayFormat: "dd/MM/yyyy",
                        width: "100%"
                    },
                    validationRules: [{ type: "required" }]
                },
                {
                    dataField: "hora_inicio",
                    label: {
                        text: "Entrada"
                    },
                    editorType: "dxDateBox",
                    editorOptions: {
                        type: "time",
                        width: "100%"
                    },
                    validationRules: [{ type: "required" }]
                },
                {
                    dataField: "hora_fin",
                    label: {
                        text: "Salida"
                    },
                    editorType: "dxDateBox",
                    editorOptions: {
                        type: "time",
                        width: "100%"
                    },
                    validationRules: [{ type: "required" }]
                },
                {
                    dataField: "paradas",
                    label: {
                        text: "Paradas"
                    },
                    editorType: "dxDataGrid",
                    editorOptions: {
                        dataSource: [],
                        editing: {
                            mode: "row",
                            allowUpdating: true,
                            allowDeleting: true,
                            allowAdding: true
                        },
                        columns: [
                            {
                                caption: "Tipo parada",
                                dataField: "tipo_parada",
                            },
                            {
                                caption: "Inicio",
                                dataField: "hora_inicio",
                                editorType: "dxDateBox",
                                editorOptions: {
                                    type: "time",
                                    width: "100%"
                                }
                            },
                            {
                                caption: "Fin",
                                dataField: "hora_fin",
                                editorType: "dxDateBox",
                                editorOptions: {
                                    type: "time",
                                    width: "100%"
                                }
                            },
                        ],
                        onSaving: function (e) {
                            console.log(e);
                            var change = e.changes[0];

                            if (change) {
                                e.cancel = true;
                                var paradas = e.component.option("dataSource");

                                console.log(change.type);
                                if(change.type === "insert") {
                                    paradas.push(change["data"]);
                                    var formData = $("#form-registro-horas").dxForm('instance').option('formData');
                                    formData["paradas"] = paradas;
                                }

                                e.component.option({
                                    dataSource: paradas,
                                    editing: {
                                        editRowKey: null,
                                        changes: []
                                    }
                                });
                            }
                        },
                    }
                },
                {
                    dataField: "unidades_realizadas",
                    label: {
                        text: "Unidades realizadas"
                    },
                    editorType: "dxNumberBox",
                    editorOptions: {
                        showSpinButtons: true,
                        width: "100%"
                    }
                },
                {
                    dataField: "observaciones",
                    label: {
                        text: "Observaciones"
                    },
                    editorType: "dxTextArea",
                    editorOptions: {
                        height: 90,
                        width: "100%"
                    }
                },
                {
                    itemType: "button",
                    horizontalAlignment: "center",
                    buttonOptions: {
                        text: "Registrar",
                        type: "success",
                        useSubmitBehavior: true,
                        onClick: function (e){
                            e.cancel = true;
                            var data = $('#form-registro-horas').dxForm('instance').option('formData');

                            console.log(data);

                            ajax.jsonRpc("/api/time/register", 'call', data)
                            .then(function(result) {
                                var data = $.parseJSON(result);
//                                DevExpress.ui.notify("Ha iniciado un registro de tiempo");
                            });
                        }
                    }
                }
            ]
        });
    }

    function sendRequest(url, params) {
        var d = $.Deferred();
        params = params || {};

        ajax.jsonRpc(url, 'call', params)
        .then(function(result) {
            var data = $.parseJSON(result);
            console.log()
            d.resolve({'data': data["data"], 'totalCount': data["totalCount"] });
        });
//        .fail(function(xhr) {
//            d.reject(xhr.responseJSON ? xhr.responseJSON.Message : xhr.statusText);
//        });

        return d.promise();
    }

    function iniciar_tiempo(params){
        params = params || {};
        ajax.jsonRpc("/api/time/start", 'call', params)
        .then(function(result) {
            var data = $.parseJSON(result);
            if(data["result"] == "ok"){
                DevExpress.ui.notify("Ha iniciado un registro de tiempo");
            }else{
                DevExpress.ui.notify("Ya hay un tiempo iniciado para ese proyecto.", "error");
            }
        });
    }

    function parar_tiempo(params){
        params = params || {};
        ajax.jsonRpc("/api/time/stop", 'call', params)
        .then(function(result) {
            var data = $.parseJSON(result);
            if(data["result"] == "ok"){
                DevExpress.ui.notify("Ha parado el tiempo");
            }else{
                DevExpress.ui.notify("No hay ningun tiempo iniciado para ese proyecto.", "error");
            }
        });
    }
});

});
