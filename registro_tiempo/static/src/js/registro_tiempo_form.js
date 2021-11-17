odoo.define('registro_tiempo.form', function (require) {
"use strict";

var ajax = require('web.ajax');

$(function() {
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
    
    function project_data_source(){
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
        return projectDataSource;
    }
    
    function project_id_load(projectDataSource){
        return $("#project_id_dx").dxSelectBox({
            dataSource: projectDataSource,
            displayExpr: "name",
            valueExpr: "id",
            searchEnabled: true,
            onValueChanged: function(data) {
                if($("#grid-registro").length){
                    $("#grid-registro").dxDataGrid('instance').refresh();
                }
                
                if($("#fecha_entrada_dx").dxDateBox("instance").option("value") == null){
                    $("#fecha_entrada_dx").dxDateBox("instance").option("value", new Date());
                }
                
                if($(".form_fields")){
                    if(data.value){
                        $(".form_fields").show();
                    }else{
                        $(".form_fields").hide();
                    }
                }
            }
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "El proyecto es obligatorio."
            }]
        }).dxSelectBox("instance");
    }
    
    function tipo_load(){
        return $("#tipo_dx").dxRadioGroup({
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
    }
    
    function covid_load(){
        return $("#covid_dx").dxCheckBox({}).dxCheckBox("instance");
    }
    
    var today = new Date();
    var tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    function fecha_entrada_load(){
        return $("#fecha_entrada_dx").dxDateBox({
            type: "date",
            displayFormat: "dd/MM/yyyy",
            max: tomorrow,
            pickerType: "rollers",
            onValueChanged: function(data) {
                var fecha = new Date(data.value);
                var fecha_salida_inp = $("#fecha_salida_dx").dxDateBox("instance");
                fecha_salida_inp.option("value", fecha);
                var fecha_str = date_to_string(fecha);
                var project_id = $("#project_id_dx").dxSelectBox("instance").option("value");
                var tipo = $("#tipo_dx").dxRadioGroup("instance").option("value");

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
                    'fecha': fecha_str
                }

                ajax.jsonRpc("/api/calendario/hora_dia_semana", 'call', params)
                .then(function(result) {
                    var data = $.parseJSON(result);
                    fecha.setHours(data["desde_hora"], data["desde_min"]);
                    $("#hora_entrada_dx").dxDateBox("instance").option("value", fecha);
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
    }
    
    function hora_entrada_load(){
        return $("#hora_entrada_dx").dxDateBox({
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
    }
    
    function fecha_salida_load(){
        return $("#fecha_salida_dx").dxDateBox({
            type: "date",
            displayFormat: "dd/MM/yyyy",
            max: tomorrow,
            pickerType: "rollers",
            onValueChanged: function(data) {
                var label = "Fecha salida";
                var fecha = new Date(data.value);
                var fecha_str = date_to_string(fecha);
                var project_id = $("#project_id_dx").dxSelectBox("instance").option("value");
                var tipo = $("#tipo_dx").dxRadioGroup("instance").option("value");

                if(!data.value || data.value == undefined || !project_id || project_id == undefined){
                    DevExpress.ui.notify("Tiene que seleccionar un proyecto.", "error");
                    return;
                }

                var params = {
                    'project_id': project_id,
                    'fecha': fecha_str
                }

                ajax.jsonRpc("/api/calendario/hora_dia_semana", 'call', params)
                .then(function(result) {
                    var data = $.parseJSON(result);
                    fecha.setHours(data["hasta_hora"], data["hasta_min"]);
                    $("#hora_salida_dx").dxDateBox("instance").option("value", fecha);
                });
            },
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La fecha de salida es obligatoria."
            }]
        }).dxDateBox("instance");
    }
    
    function hora_salida_load(){
        return $("#hora_salida_dx").dxDateBox({
            type: "time",
            displayFormat: "HH:mm",
            pickerType: "rollers",
        }).dxValidator({
            validationRules: [{
                type: "required",
                message: "La hora de salida es obligatoria."
            }]
        }).dxDateBox("instance");
    }
    
    function paradas_dx(tipoParadaSource){
        return $("#paradas_dx").dxDataGrid({
            dataSource: [],
            onInitNewRow: function (e) {
                e.data.fecha_entrada = fecha_entrada_dx.option("value");
                e.data.fecha_salida = fecha_entrada_dx.option("value");
            },
            editing: {
                mode: "cell",
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
    }
    
    function unidades_realizadas_load(){
        return $("#unidades_realizadas_dx").dxNumberBox({
            showSpinButtons: true,
            width: "100%"
        }).dxNumberBox("instance");
    }
    
    function observaciones_load(){
        return $("#observaciones_dx").dxTextArea({
            height: 90,
            width: "100%",
        }).dxTextArea("instance");
    }
    
    function tareas_load(){
        return $("#tareas_dx").dxTextArea({
            height: 90,
            width: "100%"
        }).dxTextArea("instance");
    }
    
    function btn_enviar_load(){
        return $("#btn_enviar_dx").dxButton({
            stylingMode: "contained",
            text: "Enviar",
            type: "success",
            useSubmitBehavior: true,
        }).dxButton("instance");
    }
    
    function btn_limpiar_load(){
        return $("#btn_limpiar_dx").dxButton({
            stylingMode: "contained",
            text: "Limpiar",
            type: "normal",
            onClick: function() {
                project_id_dx.option("value", null);
                tipo_dx.option("value", "Parte");
                paradas_dx.option("dataSource", []);
                unidades_realizadas_dx.reset();
                observaciones_dx.reset();
                tareas_dx.reset();
            }
        }).dxButton("instance");
    }
    
    if($("#o_page_ficha_registro_hora").length){
        var observaciones_dx;
        var project_id_dx;
        var projectDataSource = project_data_source();
        var unidades_realizadas_dx;
        var tipo_dx;
        var covid_dx;
        var fecha_entrada_dx;
        var hora_entrada_dx;
        var fecha_salida_dx;
        var hora_salida_dx;
        var paradas_dx;
        var tareas_dx; 
        
        var tiempo_id = $("#input_tiempo_id").val();
        ajax.jsonRpc("/api/time-data/" + tiempo_id, 'call', {})
        .then(function(result) {
            var data = $.parseJSON(result);
            console.log(data);
            
            project_id_dx = project_id_load(projectDataSource);
            tipo_dx = tipo_load();
            covid_dx = covid_load();
            observaciones_dx = observaciones_load();
            unidades_realizadas_dx = unidades_realizadas_load();
            fecha_entrada_dx = fecha_entrada_load();
            hora_entrada_dx = hora_entrada_load();
            fecha_salida_dx = fecha_salida_load();
            hora_salida_dx = hora_salida_load();
            tareas_dx = tareas_load();
            
//             if(data.project_id){
//                 project_id_dx.option('value', '760');
//             }
            
            if(data.fecha_hora_entrada){
                var fecha_entrada_aux = data.fecha_hora_entrada.split(" ");
                fecha_entrada_dx.option('value', fecha_entrada_aux[0]);
                hora_entrada_dx.option('value', fecha_entrada_aux[1]);
            }

            if(data.fecha_hora_salida){
                var fecha_salida_aux = data.fecha_hora_salida.split(" ");
                fecha_salida_dx.option('value', fecha_salida_aux[0]);
                hora_salida_dx.option('value', fecha_salida_aux[1]);
            }
            
            if(data.tareas){
                tareas_dx.option('value', data.tareas);
            }
            
            if(data.observaciones){
                observaciones_dx.option('value', data.observaciones)
            }
            
            if(data.unidades_realizadas){
                unidades_realizadas_dx.option('value', data.unidades_realizadas);
            }
            
            if(data.covid){
                covid_dx.option('value', data.covid);
            }
            
            if(data.tipo){
                tipo_dx.option('value', data.tipo);
            }
            
//             paradas_dx = paradas_dx(tipoParadaSource, data.paradas);
            

        });
        
        var btn_enviar_dx = btn_enviar_load();
        var btn_limpiar_dx = btn_limpiar_load();

        $("#form-registro-horas").on("submit", function(e) {
            e.preventDefault();
            var hora_entrada = hora_entrada_dx.option("value");
            var hora_salida = hora_salida_dx.option("value");
            
            console.log(hora_entrada);
            console.log(hora_salida);
            
            var params = {
                'project_id': project_id_dx.option("value"),
                'fecha_entrada': date_to_string(fecha_entrada_dx.option("value")),
                'hora_entrada': hora_entrada,
                'fecha_salida': date_to_string(fecha_salida_dx.option("value")),
                'hora_salida': hora_salida,
                'tipo': tipo_dx.option("value"),
                //'paradas': paradas_dx.option('dataSource'),
                'unidades_realizadas': unidades_realizadas_dx.option("value"),
                'observaciones': observaciones_dx.option("value"),
                'tareas': tareas_dx.option("value"),
                'covid': covid_dx.option("value"),
            };

            ajax.jsonRpc("/api/time/edit/" + tiempo_id, 'call', params)
            .then(function(result) {
                var data = $.parseJSON(result);
                if(data["result"] == "ok"){
                    DevExpress.ui.notify("Ha registrado el tiempo correctamente");
                    fecha_entrada_dx.option("value", date_to_string(fecha_entrada_dx.option("value"), 0));

//                     var paradas = paradas_dx.option('dataSource');
//                     if(paradas != undefined){
//                         $.each(paradas, function( index, value ) {
//                             paradas[index]["fecha_entrada"] =  date_to_string(value["fecha_entrada"], 1);
//                             paradas[index]["fecha_salida"] = date_to_string(value["fecha_salida"], 1);
//                         });
//                         paradas_dx.option('dataSource', paradas);
//                     }

                    //grid_resgistro_dx.refresh();
                }else{
                    DevExpress.ui.notify("Error. No se ha podido registrar el tiempo.", "error");
                }
            });
        });
    }

    if($("#o_page_registro_horas").length){
        console.log("no tiene que entrar");
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

        var tecnicosDataSource = new DevExpress.data.CustomStore({
            key: "id",
            load: function(loadOptions) {
                var params = {
                    "offset": loadOptions.skip,
                    "limit": loadOptions.take,
                }

                if(loadOptions.searchValue){
                    params["search"] = loadOptions.searchValue;
                }

                return sendRequest("/api/tecnicos-proyecto", params);
            },
        });

        $("#summary").dxValidationSummary({});

        var projectDataSource = project_data_source();

        var project_id_dx = project_id_load(projectDataSource);
        var tipo_dx = tipo_load();
        var covid_dx = covid_load();
        var fecha_entrada_dx = fecha_entrada_load();
        var hora_entrada_dx = hora_entrada_load();
        var fecha_salida_dx = fecha_salida_load();
        var hora_salida_dx = hora_salida_load();

        var paradas_dx = $("#paradas_dx").dxDataGrid({
            dataSource: [],
            onInitNewRow: function (e) {
                e.data.fecha_entrada = fecha_entrada_dx.option("value");
                e.data.fecha_salida = fecha_entrada_dx.option("value");
            },
            editing: {
                mode: "cell",
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

        var unidades_realizadas_dx = unidades_realizadas_load();
        var observaciones_dx = observaciones_load();
        var tareas_dx = tareas_load();
        var btn_enviar_dx = btn_enviar_load();

        var btn_limpiar_dx = $("#btn_limpiar_dx").dxButton({
            stylingMode: "contained",
            text: "Limpiar",
            type: "normal",
            onClick: function() {
                project_id_dx.option("value", null);
                tipo_dx.option("value", "Parte");
                paradas_dx.option("dataSource", []);
                unidades_realizadas_dx.reset();
                observaciones_dx.reset();
                tareas_dx.reset();
            }
        }).dxButton("instance");

        $("#form-registro-horas").on("submit", function(e) {
            e.preventDefault();
            var hora_entrada = hora_entrada_dx.option("value");
            var hora_salida = hora_salida_dx.option("value");
            
            var params = {
                'project_id': project_id_dx.option("value"),
                'fecha_entrada': date_to_string(fecha_entrada_dx.option("value")),
                'hora_entrada': hora_entrada.getHours() + ":" + hora_entrada.getMinutes(),
                'fecha_salida': date_to_string(fecha_salida_dx.option("value")),
                'hora_salida': hora_salida.getHours() + ":" + hora_salida.getMinutes(),
                'tipo': tipo_dx.option("value"),
                'paradas': paradas_dx.option('dataSource'),
                'unidades_realizadas': unidades_realizadas_dx.option("value"),
                'observaciones': observaciones_dx.option("value"),
                'tareas': tareas_dx.option("value"),
                'covid': covid_dx.option("value"),
            };

            ajax.jsonRpc("/api/time/register", 'call', params)
            .then(function(result) {
                var data = $.parseJSON(result);
                if(data["result"] == "ok"){
                    DevExpress.ui.notify("Ha registrado el tiempo correctamente");
                    fecha_entrada_dx.option("value", date_to_string(fecha_entrada_dx.option("value"), 0));

                    var paradas = paradas_dx.option('dataSource');
                    if(paradas != undefined){
                        $.each(paradas, function( index, value ) {
                            paradas[index]["fecha_entrada"] =  date_to_string(value["fecha_entrada"], 0);
                            paradas[index]["fecha_salida"] = date_to_string(value["fecha_salida"], 0);
                        });
                        paradas_dx.option('dataSource', paradas);
                    }

                    grid_resgistro_dx.refresh();
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
                        'project_id': project_id_dx.option("value")
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
//                 {
//                     width: 75,
//                     alignment: 'center',
//                     cellTemplate: function (container, options) {
//                         $('<a/>').addClass('dx-link')
//                                 .text('Editar')
//                                 .attr('href', "/my/timesheet/" + options.data.id)
//                                 .appendTo(container);
//                     },
//                     editCellTemplate: function(e){
//                         return false;
//                     }
//                 }
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

    function date_to_string(fecha, sum_day){
        sum_day = sum_day || 0;
        var f = new Date(fecha);
        if(sum_day > 0){
            f.setDate(f.getDate() + sum_day);
        }
        return f.getFullYear() + "-" + (f.getMonth() + 1) + "-" + f.getDate();
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
