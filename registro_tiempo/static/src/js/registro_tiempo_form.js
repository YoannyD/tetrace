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
    }

    if($("#o_page_registro_horas").length){
        initGeolocation();

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

        $("#summary").dxValidationSummary({});

        var project_id_dx = $("#project_id_dx").dxSelectBox({
            dataSource: projectDataSource,
            displayExpr: "name",
            valueExpr: "id",
            searchEnabled: true,
            onValueChanged: function(data) {
                if(data.value){
                    $(".form_fields").show();
                }else{
                    $(".form_fields").hide();
                }
            }
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "El proyecto es obligatorio."
            }]
        }).dxSelectBox("instance");

        var tipo_dx = $("#tipo_dx").dxRadioGroup({
            layout: "horizontal",
            items: ["Parte", "MOB", "DEMOB"],
            value: "Parte"
        }).dxRadioGroup("instance");

        var fecha_entrada_dx = $("#fecha_entrada_dx").dxDateBox({
            type: "datetime",
            displayFormat: "dd/MM/yyyy HH:mm",
            width: "100%",
            visible: true,
            onValueChanged: function(data) {
                var f = new Date(data.value);
                var fecha = f.getFullYear() + "-" + (f.getMonth() + 1) + "-" + f.getDate();
                var project_id = project_id_dx.option("value");
                var tipo = tipo_dx.option("value");

                if(tipo != 'Parte'){
                    return;
                }

                if(!data.value || data.value == undefined || !project_id || project_id == undefined){
                    DevExpress.ui.notify("Tiene que seleccionar un proyecto.", "error");
                    return;
                }

                var params = {
                    'project_id': project_id,
                    'fecha': fecha
                }
                console.log(params);
                ajax.jsonRpc("/api/calendario/hora_dia_semana", 'call', params)
                .then(function(result) {
                    var data = $.parseJSON(result);
                    f.setHours(data["desde_hora"], data["desde_min"]);
                    fecha_entrada_dx.option("value", f);
                });

                var text_label = "Fecha entrada <br/>";
                if(f.getHours() >= 22){
                    text_label += ' <span class="badge badge-dark">Nocturno</span>'
                }

                ajax.jsonRpc("/api/festivo", 'call', params)
                .then(function(result) {
                    var data = $.parseJSON(result);
                    if(data["festivo"]){
                        text_label += ' <span class="badge badge-danger">Festivo</span>';
                    }
                    $(".dx-field-fecha_entrada .dx-field-label").html(text_label);
                });
            },
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La fecha de entrada es obligatoria."
            }]
        }).dxDateBox("instance");

        var fecha_salida_dx = $("#fecha_salida_dx").dxDateBox({
            type: "datetime",
            displayFormat: "dd/MM/yyyy HH:MM",
            width: "100%",
            visible: true,
            onValueChanged: function(data) {
                var f = new Date(data.value);
                var fecha = f.getFullYear() + "-" + (f.getMonth() + 1) + "-" + f.getDate();
                var project_id = project_id_dx.option("value");
                var tipo = tipo_dx.option("value");

                if(tipo != 'Parte'){
                    return;
                }

                if(!data.value || data.value == undefined || !project_id || project_id == undefined){
                    DevExpress.ui.notify("Tiene que seleccionar un proyecto.", "error");
                    return;
                }

                var params = {
                    'project_id': project_id,
                    'fecha': fecha
                }

                ajax.jsonRpc("/api/calendario/hora_dia_semana", 'call', params)
                .then(function(result) {
                    var data = $.parseJSON(result);
                    f.setHours(data["hasta_hora"], data["hasta_min"]);
                    fecha_salida_dx.option("value", f);
                });
            },
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La fecha de salida es obligatoria."
            }]
        }).dxDateBox("instance");

        var paradas_dx = $("#paradas_dx").dxDataGrid({
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
        }).dxDataGrid("instance");

        var unidades_realizadas_dx = $("#unidades_realizadas_dx").dxNumberBox({
            showSpinButtons: true,
            width: "100%"
        }).dxNumberBox("instance");

        var observaciones_dx = $("#observaciones_dx").dxTextArea({
            height: 90,
            width: "100%"
        }).dxTextArea("instance");

        var btn_enviar_dx = $("#btn_enviar_dx").dxButton({
            stylingMode: "contained",
            text: "Enviar",
            type: "success",
            useSubmitBehavior: true,
        }).dxButton("instance");

        $("#form-registro-horas").on("submit", function(e) {
            e.preventDefault();
            var params = {
                'project_id': project_id_dx.option("value"),
                'fecha_entrada': fecha_entrada_dx.option("value"),
                'fecha_salida': fecha_salida_dx.option("value"),
                'tipo': tipo_dx.option("value"),
                'paradas': paradas_dx.option('dataSource'),
                'unidades_realizadas': unidades_realizadas_dx.option("value"),
                'observaciones': observaciones_dx.option("value"),
            };

            ajax.jsonRpc("/api/time/register", 'call', params)
            .then(function(result) {
                var data = $.parseJSON(result);
                if(data["result"] == "ok"){
                    DevExpress.ui.notify("Ha registrado el tiempo correctamente");
//                    e.reset();
                }else{
                    DevExpress.ui.notify("Error. No se ha podido registrar el tiempo.", "error");
                }
            });
        });

        $("#grid-registro").dxDataGrid({
            dataSource: new DevExpress.data.CustomStore({
                key: "id",
                load: function(loadOptions) {
                    console.log(loadOptions);
                    var params = {
                        "offset": loadOptions.skip,
                        "limit": loadOptions.take,
                    }

                    if(loadOptions.filter){
                        params["filtros"] = loadOptions.filter;
                    }

                    if(loadOptions.group){
                        params["group"] = loadOptions.group;
                    }

                    if(loadOptions.isLoadingAll){
                        params["isLoadingAll"] = loadOptions.isLoadingAll;
                    }

                    params['order'] = '';
                    $.each(loadOptions.sort, function( index, value ) {
                        if(index > 0){
                            params['order'] += ", ";
                        }
                        params['order'] += value["selector"];
                        if(value["desc"])
                            params['order'] += " desc";
                    });

                    return sendRequest2("/api/registros", params);
                },
            }),
            remoteOperations: { groupPaging: true },
            allowColumnReordering: true,
            allowColumnResizing: true,
            rowAlternationEnabled: true,
            showColumnLines: true,
            showRowLines: true,
            showBorders: true,
            repaintChangesOnly: true,
            grouping: {autoExpandAll: false,},
            groupPanel: {visible: true},
            searchPanel: {visible: true},
            filterRow: {
                visible: true,
                applyFilter: "auto"
            },
            headerFilter: {
                visible: true
            },
            wordWrapEnabled: true,
            scrolling: {
                mode: "virtual",
                rowRenderingMode: "virtual"
            },
            paging: {
                pageSize: 50
            },
            summary: {
                groupItems: [{
                    column: "id",
                    summaryType: "count"
                }]
            },
            columns: [
                {
                    caption: "Projecto",
                    dataField: "project_name",
                },
                {
                    caption: "Tipo",
                    dataField: "tipo",
                },
                {
                    caption: "Festivo",
                    dataField: "festivo",
                },
                {
                    caption: "Nocturno",
                    dataField: "nocturno",
                },
                {
                    caption: "Entrada",
                    dataField: "fecha_entrada",
                    dataType: "date",
                },
                {
                    caption: "Día",
                    dataField: "dia_semana_fecha_entrada",
                },
                {
                    caption: "Salida",
                    dataField: "fecha_salida",
                    dataType: "date",
                },
                {
                    caption: "Horas",
                    dataField: "horas_trabajadas",
                },
                {
                    caption: "Horas extra",
                    dataField: "horas_extra",
                },
            ],
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

    function sendRequest2(url, params) {
        var d = $.Deferred();
        params = params || {};

        ajax.jsonRpc(url, 'call', params)
        .then(function(result) {
            var data = $.parseJSON(result);
            d.resolve(data);
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
