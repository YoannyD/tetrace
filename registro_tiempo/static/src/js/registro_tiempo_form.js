odoo.define('registro_tiempo.form', function (require) {
"use strict";

require('web_editor.ready');
var base = require('web_editor.base');
var ajax = require('web.ajax');

base.ready().then(function () {
    DevExpress.localization.locale(navigator.language || navigator.browserLanguage);
    DevExpress.ui.dxOverlay.baseZIndex(2000);
    DevExpress.config({ defaultCurrency: "EUR" });

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
                if(fecha_entrada_dx.option("value") == null){
                    var fecha_entrada = fecha_entrada_dx.option("value", new Date());
                }
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
            value: "Parte",
            onValueChanged: function(data) {
                if(data.value != 'Parte'){
                    $(".dx-field-fecha_entrada .dx-field-label").html("Fecha entrada");
                    $(".dx-field-hora_entrada .dx-field-label").html("Hora entrada");
                    $(".dx-field-fecha_salida .dx-field-label").html("Fecha salida");
                    $(".dx-field-hora_entrada .dx-field-label").html("Hora entrada");
                    $(".dx-field-paradas").hide();
                    $(".dx-field-unidades_realizadas").hide();
                }else{
                    fecha_entrada_dx.option("onValueChanged");
                    $(".dx-field-paradas").show();
                    $(".dx-field-unidades_realizadas").show();
                }
            }
        }).dxRadioGroup("instance");

        var fecha_entrada_dx = $("#fecha_entrada_dx").dxDateBox({
            type: "date",
            displayFormat: "dd/MM/yyyy",
            pickerType: "rollers",
            onValueChanged: function(data) {
                var f = new Date(data.value);
                fecha_salida_dx.option("value", f);
                var fecha = f.getFullYear() + "-" + (f.getMonth() + 1) + "-" + f.getDate();
                var project_id = project_id_dx.option("value");
                var tipo = tipo_dx.option("value");

                var label = "Fecha entrada";
                if(tipo != 'Parte'){
                    $(".dx-field-fecha_entrada .dx-field-label").html(label);
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
                    f.setHours(data["desde_hora"], data["desde_min"]);
                    hora_entrada_dx.option("value", f);
                });

                ajax.jsonRpc("/api/festivo", 'call', params)
                .then(function(result) {
                    var data = $.parseJSON(result);
                    if(data["festivo"]){
                        label += ' <span class="badge badge-danger">Festivo</span>';
                    }
                    $(".dx-field-fecha_entrada .dx-field-label").html(label);
                });
            },
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La fecha de entrada es obligatoria."
            }]
        }).dxDateBox("instance");

        var hora_entrada_dx = $("#hora_entrada_dx").dxDateBox({
            type: "time",
            displayFormat: "HH:mm",
            pickerType: "rollers",
            onValueChanged: function(data) {
                var f = new Date(data.value);
                var label = "Hora entrada";
                if(es_hora_nocturna(f.getHours())){
                    label += ' <span class="badge badge-dark">Nocturno</span>';
                }
                $(".dx-field-hora_entrada .dx-field-label").html(label);
            },
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La fecha de entrada es obligatoria."
            }]
        }).dxDateBox("instance");

        var fecha_salida_dx = $("#fecha_salida_dx").dxDateBox({
            type: "date",
            displayFormat: "dd/MM/yyyy",
            pickerType: "rollers",
            onValueChanged: function(data) {
                var label = "Fecha salida";
                var f = new Date(data.value);
                var fecha = f.getFullYear() + "-" + (f.getMonth() + 1) + "-" + f.getDate();
                var project_id = project_id_dx.option("value");
                var tipo = tipo_dx.option("value");

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
                    hora_salida_dx.option("value", f);
                });
            },
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La fecha de salida es obligatoria."
            }]
        }).dxDateBox("instance");

        var hora_salida_dx = $("#hora_salida_dx").dxDateBox({
            type: "time",
            displayFormat: "HH:mm",
            pickerType: "rollers",
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La hora de salida es obligatoria."
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
                    dataType: "datetime",
                },
                {
                    caption: "Salida",
                    dataField: "fecha_salida",
                    dataType: "datetime",
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
            var hora_entrada = hora_entrada_dx.option("value");
            var hora_salida = hora_salida_dx.option("value");

            var params = {
                'project_id': project_id_dx.option("value"),
                'fecha_entrada': fecha_entrada_dx.option("value"),
                'hora_entrada': hora_entrada.getHours() + ":" + hora_entrada.getMinutes(),
                'fecha_salida': fecha_salida_dx.option("value"),
                'hora_salida': hora_salida.getHours() + ":" + hora_salida.getMinutes(),
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
                    tipo_dx.option("value", "Parte");
                    paradas_dx.option("dataSource", []);
                    unidades_realizadas_dx.reset();
                    observaciones_dx.reset();
                    grid_resgistro_dx.refresh();
                    project_id_dx.reset();
                }else{
                    DevExpress.ui.notify("Error. No se ha podido registrar el tiempo.", "error");
                }
            });
        });

        var grid_resgistro_dx = $("#grid-registro").dxDataGrid({
            dataSource: new DevExpress.data.CustomStore({
                key: "id",
                load: function(loadOptions) {
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
            remoteOperations: { groupPaging: true,},
            allowColumnReordering: true,
            allowColumnResizing: true,
            rowAlternationEnabled: true,
            showColumnLines: true,
            showRowLines: true,
            showBorders: true,
            repaintChangesOnly: true,
            wordWrapEnabled: true,
            grouping: {
                autoExpandAll: false,
            },
            groupPanel: {visible: true},
            searchPanel: {visible: true},
            filterRow: {
                visible: true,
                applyFilter: "auto"
            },
            headerFilter: {
                visible: true
            },
            scrolling: {
                mode: "virtual",
                rowRenderingMode: "virtual"
            },
            paging: {
                pageSize: 50
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
                    caption: "Día",
                    dataField: "dia_semana_fecha_entrada",
                },
                {
                    caption: "Entrada",
                    dataField: "fecha_hora_entrada",
                    dataType: "datetime",
                    format: "dd/MM/yyyy HH:mm",
                    allowFiltering: true,
                    allowGrouping: false
                },
                {
                    caption: "Salida",
                    dataField: "fecha_hora_salida",
                    dataType: "datetime",
                    format: "dd/MM/yyyy HH:mm",
                    allowFiltering: true,
                    allowGrouping: false
                },
                {
                    caption: "Horas",
                    dataField: "horas_trabajadas",
                },
                {
                    caption: "Horas extra",
                    dataField: "horas_extra",
                },
                {
                    caption: "Horas extra cliente",
                    dataField: "horas_extra_cliente",
                },
            ],
            summary: {
                groupItems: [{
                    column: "id",
                    summaryType: "count"
                }]
            },
        }).dxDataGrid('instance');
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

    function es_hora_nocturna(hora){
        if(hora < 6 || hora >= 22)
            return true;
        return false;
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
