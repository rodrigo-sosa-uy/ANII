% =========================================================================
% SCRIPT DE ANÁLISIS SEMANAL DE CLIMA (7 DÍAS - OPENWEATHER)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Nombre de la carpeta con los archivos (Debe seguir formato: "YYYY_MM_DD to YYYY_MM_DD")
folder_name = '2025_12_08 to 2025_12_14';

% -------------------------------------------------------------------------

% 1. Configuración de Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

target_dir = fullfile(script_path, folder_name);
fprintf('Analizando periodo: %s\n', folder_name);

if ~isfolder(target_dir)
    error('La carpeta "%s" no existe.', folder_name);
end

% 2. Parsear fechas desde el nombre de la carpeta
try
    parts = strsplit(folder_name, ' to ');
    t_range_start = datetime(parts{1}, 'InputFormat', 'yyyy_MM_dd');
    t_range_end = datetime(parts{2}, 'InputFormat', 'yyyy_MM_dd');
    
    % Generar lista de días consecutivos
    num_days = days(t_range_end - t_range_start) + 1;
    date_list = t_range_start + caldays(0:num_days-1);
    
    fprintf('Se graficarán %d días (del %s al %s).\n', num_days, datestr(t_range_start), datestr(t_range_end));
catch
    error('El nombre de la carpeta debe tener el formato "YYYY_MM_DD to YYYY_MM_DD"');
end

% 3. Preparar Figura
fig = figure('Name', 'Resumen Semanal de Clima', 'Color', 'w', 'Position', [50, 50, 1000, 1200]);

% Estructura para el reporte de texto
stats_log = struct(); 
dummy_date = '2000-01-01'; % Para alinear eje X
t_start_dummy = datetime(dummy_date + " 00:00:00", 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
t_end_dummy   = datetime(dummy_date + " 23:59:59", 'InputFormat', 'yyyy-MM-dd HH:mm:ss');

% Variables para la leyenda (se asignan en el primer bucle válido)
p1 = []; p2 = []; a = [];

% -------------------------------------------------------------------------
% 4. BUCLE DE PROCESAMIENTO (Día a Día)
% -------------------------------------------------------------------------

for i = 1:num_days
    current_dt = date_list(i);
    
    % Nombre esperado: 2025_12_08_weather.csv (Matlab datestr usa yyyy_mm_dd)
    date_str_file = datestr(current_dt, 'yyyy_mm_dd'); 
    date_display = datestr(current_dt, 'yyyy-mm-dd');
    
    filename = [date_str_file, '_weather.csv'];
    full_path = fullfile(target_dir, filename);
    
    % --- SUBPLOT DEL DÍA ---
    subplot(num_days, 1, i);
    hold on;
    
    % Comprobar existencia
    file_exists = isfile(full_path);
    
    if file_exists
        % --- LEER DATOS ---
        opts = detectImportOptions(full_path);
        opts.VariableNamingRule = 'preserve';
        data = readtable(full_path, opts);
        
        if isempty(data)
            file_exists = false; % Archivo vacío se trata como inexistente
        else
            raw_time = data{:, 1};
            conds = data{:, 2};
            temps = data{:, 4};
            hums  = data{:, 5};
            clouds= data{:, 6};
            
            % Tiempo dummy
            time_str = string(raw_time);
            t = datetime(dummy_date + " " + time_str, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
            
            % Eje Derecho: Nubes y Humedad
            yyaxis right
            a = area(t, clouds, 'FaceColor', [0.8 0.8 0.8], 'FaceAlpha', 0.4, 'EdgeColor', 'none');
            p1 = plot(t, hums, 'Color', '#0072BD', 'LineWidth', 1.2, 'LineStyle', '--');
            ylim([0 100]);
            set(gca, 'YColor', '#0072BD');

            % Eje Izquierdo: Temperatura
            yyaxis left
            p2 = plot(t, temps, 'Color', '#D95319', 'LineWidth', 1.5);
            ylim([min(temps)-2, max(temps)+2]);
            set(gca, 'YColor', '#D95319');
            
            % Info textual
            clim_pred = char(mode(categorical(conds)));
            info_str = sprintf(' %s | %s | Max: %.1f°C', date_display, clim_pred, max(temps));
            text(t_start_dummy + minutes(15), max(temps)+0.5, info_str, ...
                'BackgroundColor', 'w', 'EdgeColor', 'k', 'FontSize', 9, 'VerticalAlignment', 'top');
            
            % Guardar stats
            stats_log(i).Fecha = date_display;
            stats_log(i).Temp_Max = max(temps);
            stats_log(i).Temp_Min = min(temps);
            stats_log(i).Temp_Avg = mean(temps);
            stats_log(i).Hum_Avg = mean(hums);
            stats_log(i).Cloud_Avg = mean(clouds);
            stats_log(i).Clima = clim_pred;
            stats_log(i).TieneDatos = true;
        end
    end
    
    if ~file_exists
        % --- CASO SIN DATOS (GRÁFICO VACÍO) ---
        % Configurar ejes vacíos para mantener estructura
        yyaxis right
        ylim([0 100]); set(gca, 'YColor', [0.7 0.7 0.7]);
        yticks([]); % Ocultar ticks derechos
        
        yyaxis left
        ylim([0 40]); set(gca, 'YColor', [0.7 0.7 0.7]);
        yticks([]); % Ocultar ticks izquierdos
        
        % Texto informativo
        text(t_start_dummy + hours(12), 20, ['SIN DATOS (' date_display ')'], ...
            'HorizontalAlignment', 'center', 'Color', [0.6 0.6 0.6], 'FontWeight', 'bold');
        
        % Stats vacíos (NaN)
        stats_log(i).Fecha = date_display;
        stats_log(i).Temp_Max = NaN;
        stats_log(i).Temp_Min = NaN;
        stats_log(i).Temp_Avg = NaN;
        stats_log(i).Hum_Avg = NaN;
        stats_log(i).Cloud_Avg = NaN;
        stats_log(i).Clima = 'N/A';
        stats_log(i).TieneDatos = false;
    end
    
    % Formato Común
    grid on; grid minor;
    xtickformat('HH:mm');
    xlim([t_start_dummy, t_end_dummy]);
    
    % Etiquetas eje Y solo en el medio
    if i == round(num_days/2)
        yyaxis left; ylabel('Temp (°C)');
        yyaxis right; ylabel('Nubes/Hum (%)');
    end
    
    % Etiquetas X solo al final
    if i < num_days
        xticklabels({});
    else
        xlabel('Hora del día');
    end
end

% Añadir leyenda global si tenemos al menos un gráfico válido
if ~isempty(p2)
    subplot(num_days, 1, 1);
    legend([p2, p1, a], {'Temperatura', 'Humedad', 'Cobertura Nubosa'}, ...
           'Location', 'northoutside', 'Orientation', 'horizontal', 'Box', 'off');
end

% -------------------------------------------------------------------------
% 5. GUARDAR IMAGEN
% -------------------------------------------------------------------------
img_name = 'resumen_semanal_clima.png';
full_img_path = fullfile(target_dir, img_name);
saveas(fig, full_img_path);
fprintf('Imagen guardada en: %s\n', full_img_path);

% -------------------------------------------------------------------------
% 6. GENERAR REPORTE DE TEXTO (.txt)
% -------------------------------------------------------------------------
txt_name = 'resumen_semanal_clima.txt';
full_txt_path = fullfile(target_dir, txt_name);

fid = fopen(full_txt_path, 'w');
if fid == -1
    warning('No se pudo crear el archivo de texto.');
else
    fprintf(fid, '==========================================================\r\n');
    fprintf(fid, ' RESUMEN CLIMÁTICO SEMANAL: %s\r\n', folder_name);
    fprintf(fid, '==========================================================\r\n\r\n');
    
    % Escribir día por día
    for k = 1:length(stats_log)
        s = stats_log(k);
        fprintf(fid, '[ %s ]\r\n', s.Fecha);
        if s.TieneDatos
            fprintf(fid, '   Condición:   %s\r\n', s.Clima);
            fprintf(fid, '   Temperatura: Max %.2f°C | Min %.2f°C | Prom %.2f°C\r\n', s.Temp_Max, s.Temp_Min, s.Temp_Avg);
            fprintf(fid, '   Humedad:     %.2f %%\r\n', s.Hum_Avg);
            fprintf(fid, '   Nubosidad:   %.2f %%\r\n', s.Cloud_Avg);
        else
            fprintf(fid, '   -- SIN DATOS REGISTRADOS --\r\n');
        end
        fprintf(fid, '----------------------------------------------------------\r\n');
    end
    
    % Resumen global (solo con días válidos)
    valid_indices = [stats_log.TieneDatos];
    if any(valid_indices)
        temps_all = [stats_log(valid_indices).Temp_Max];
        [max_week, idx_local] = max(temps_all);
        
        % Re-mapear índice local al global
        valid_structs = stats_log(valid_indices);
        dia_calor = valid_structs(idx_local).Fecha;
        
        clouds_all = [stats_log(valid_indices).Cloud_Avg];
        [max_cloud, idx_local_cloud] = max(clouds_all);
        dia_nube = valid_structs(idx_local_cloud).Fecha;
        
        fprintf(fid, '\r\n>> HITOS DE LA SEMANA:\r\n');
        fprintf(fid, '🔥 Día más caluroso: %s (%.2f °C)\r\n', dia_calor, max_week);
        fprintf(fid, '☁️ Día más nublado:  %s (%.1f%% nubes)\r\n', dia_nube, max_cloud);
    else
        fprintf(fid, '\r\n>> NO HAY DATOS SUFICIENTES PARA HITOS.\r\n');
    end
    
    fclose(fid);
    fprintf('Reporte de texto guardado en: %s\n', full_txt_path);
end