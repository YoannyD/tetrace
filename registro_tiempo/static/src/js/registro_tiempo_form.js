odoo.define('registro_tiempo.form', function (require) {
"use strict";

require('web_editor.ready');
// DevExpress.localization.locale(navigator.language || navigator.browserLanguage);
//DevExpress.ui.dxOverlay.baseZIndex(2000);
//Globalize.loadMessages({'es': es});

var base = require('web_editor.base');
var ajax = require('web.ajax');

base.ready().then(function () {
    var current_position;
    var location = {};
    var mapWidget;
    function initGeolocation(){
        if( navigator.geolocation ){
            navigator.geolocation.getCurrentPosition(get_position, function(){});
        }else{
            alert("Sorry, your browser does not support geolocation services.");
        }
    }

    function get_position(position){
        current_position = position;
        mapWidget.option("markers", [{
            location: { lat: current_position.coords.latitude, lng: current_position.coords.longitude},
            tooltip: {
                text: "Tú ubicación"
            }
        }]);
        mapWidget.option("center", { lat: current_position.coords.latitude, lng: current_position.coords.longitude});
    }

    if($("#o_page_registro_horas").length){
        initGeolocation();

        if(current_position){
            location = { lat: current_position.coords.latitude, lng: current_position.coords.longitude};
        }

        mapWidget = $("#map_registro_horas").dxMap({
            provider: "bing",
            zoom: 11,
            height: 250,
            width: "100%",
            controls: true,
            markers: [{
                location: location,
                tooltip: {
                    text: "Tú ubicación"
                }
            }]
        }).dxMap("instance");

        $(".btn-registro-hora").click(function(event){
            event.preventDefault();
            var tipo = $(this).data("tipo");
            var  latitud, longitud;
            if(current_position != undefined){
                latitud = current_position.coords.latitude;
                longitud = current_position.coords.longitude;
            }
            registrar_tiempo(tipo, latitud, longitud);
        });

        $("#btn-form-regis-horas").click(function(event){
            event.preventDefault();
            $("#form-registro-horas").toggle("slow");
        });

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

        var paradaFormData;
        var formWidget = $("#form-registro-horas").dxForm({
            readOnly: false,
            showColonAfterLabel: true,
            maxColWidth: 300,
            labelLocation: "top",
            align: "center",
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
                    validationRules: [{
                        type: "required",
                        message: "El proyecto es obligatorio."
                    }]
                }, // project_id
                {
                    dataField: "fecha_entrada",
                    label: {
                        text: "Fecha entrada"
                    },
                    editorType: "dxDateBox",
                    editorOptions: {
                        type: "datetime",
                        displayFormat: "dd/MM/yyyy HH:MM",
                        width: "100%"
                    },
                    validationRules: [{
                        type: "required",
                        message: "La fecha de entrada es obligatoria."
                    }]
                }, // fecha_entrada
                {
                    dataField: "fecha_salida",
                    label: {
                        text: "Fecha salida"
                    },
                    editorType: "dxDateBox",
                    editorOptions: {
                        type: "datetime",
                        displayFormat: "dd/MM/yyyy HH:MM",
                        width: "100%"
                    },
                    validationRules: [{
                        type: "required",
                        message: "La fecha de salida es obligatoria."
                    }]
                }, // fecha_salida
                {
                    dataField: "paradas",
                    label: {
                        text: "Paradas"
                    },
                    editorType: "dxDataGrid",
                    editorOptions: {
                        elementAttr: {
                        id: "dxParadas",
                    },
                        dataSource: [],
                        editing: {
                            mode: "row",
                            allowUpdating: true,
                            allowDeleting: true,
                            allowAdding: true,
                            useIcons: true
                        },
                        columns: [
                            {
                                caption: "Tipo parada",
                                dataField: "tipo_parada_id",
                                lookup: {
                                    dataSource: tipoParadaSource,
                                    displayExpr: "name",
                                    valueExpr: "id"
                                },
                                validationRules: [{
                                    type: "required",
                                    message: "El tipo de parada es obligatorio."
                                }]
                            },
                            {
                                caption: "Entrada",
                                dataField: "fecha_entrada",
                                editorType: "dxDateBox",
                                editorOptions: {
                                    type: "datetime",
                                    displayFormat: "dd/MM/yyyy HH:mm",
                                    width: "100%"
                                }
                            },
                            {
                                caption: "Salida",
                                dataField: "fecha_salida",
                                editorType: "dxDateBox",
                                editorOptions: {
                                    type: "datetime",
                                    displayFormat: "dd/MM/yyyy HH:mm",
                                    width: "100%"
                                }
                            },
                        ],
                    }
                }, // paradas
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
                }, // unidades_realizadas
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
                }, // observacioens
                {
                    itemType: "button",
                    horizontalAlignment: "center",
                    buttonOptions: {
                        text: "Registrar",
                        type: "success",
                        useSubmitBehavior: true,
                        onClick: function (e){
                            e.cancel = true;
                            var dxFormRegistroHoras = $('#form-registro-horas').dxForm('instance');
                            if(!dxFormRegistroHoras.validate().isValid){
                                return;
                            }

                            var dxDataGridParadas = $('#dxParadas').dxDataGrid('instance');
                            var data = dxFormRegistroHoras.option('formData');
                            data["paradas"] = dxDataGridParadas.option('dataSource');

                            ajax.jsonRpc("/api/time/register", 'call', data)
                            .then(function(result) {
                                var data = $.parseJSON(result);
                                if(data["result"] == "ok"){
                                    DevExpress.ui.notify("Ha registrado el tiempo correctamente");
                                    dxFormRegistroHoras.resetValues();
                                    dxDataGridParadas.option('dataSource', []);
                                }else{
                                    DevExpress.ui.notify("Error. No se ha podido registrar el tiempo.", "error");
                                }
                            });
                        }
                    }
                } // botón
            ]
        });
    }

    function sendRequest(url, params) {
        var d = $.Deferred();
        params = params || {};

        ajax.jsonRpc(url, 'call', params)
        .then(function(result) {
            var data = $.parseJSON(result);
            d.resolve({'data': data["data"], 'totalCount': data["totalCount"] });
        });
        return d.promise();
    }

    function registrar_tiempo(tipo, latitud, longitud){
        var url = "";
        if(tipo == 'checked_out'){
            url = "/api/attendance/start";
        }else{
            url = "/api/attendance/stop";
        }
        var params = {
            latitud: latitud,
            longitud: longitud
        };
        ajax.jsonRpc(url, 'call', params)
        .then(function(result) {
            var data = $.parseJSON(result);
            if(data["result"] == "ok"){
                DevExpress.ui.notify(data["msg"]);
                cambiar_boton_registro_tiempo(tipo);
            }else{
                DevExpress.ui.notify(data["msg"], "error");
            }
        });
    }

    function cambiar_boton_registro_tiempo(tipo){
        if(tipo == "checked_in"){
            $(".btn-registro-hora")
            .removeClass("btn-danger")
            .addClass("btn-success")
            .data("tipo", "checked_out");
            $("span.txt-check-tiempo").text("entrada");
            $("#ico-registro").removeClass("fa-sign-out").addClass("fa-sign-in");
        }else{
            $(".btn-registro-hora")
            .removeClass("btn-success")
            .addClass("btn-danger")
            .data("tipo", "checked_in");
            $("span.txt-check-tiempo").text("salida");
            $("#ico-registro").removeClass("fa-sign-in").addClass("fa-sign-out");
        }

    }
});

});
