% =========================================================================
% SCRIPT PARA COMPARAR RADIACIÓN DE VARIOS DÍAS (SEMANA)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Nombre de la carpeta que contiene los archivos de la semana.
% Debe estar EN LA MISMA CARPETA que este script.
folder_name = '2025_12_01 to 2025_12_07';

% -------------------------------------------------------------------------

% 1. Configuración de Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

target_dir = fullfile(script_path, folder_name);
fprintf('Buscando archivos en: %s\n', target_dir);

% 2. Obtener lista de archivos CSV
if ~isfolder(target_dir)
    error('La carpeta "%s" no existe.', folder_name);
end

file_list = dir(fullfile(target_dir, '*.csv'));
num_files = length(file_list);

if num_files == 0
    error('No se encontraron archivos .csv en la carpeta indicada.');
end

fprintf('Se encontraron %d archivos para procesar.\n', num_files);

% 3. Preparar Gráfico
% MODIFICADO: Asignamos a 'fig' para poder guardar
fig = figure('Name', 'Comparativa Semanal de Radiación', 'Color', 'w', 'Position', [100, 100, 1000, 600]);
hold on;

% Paleta de colores para diferenciar los días (usa 'turbo', 'parula' o 'lines')
colors = turbo(num_files);

% Estructura para guardar estadísticas y mostrarlas en consola
stats_table = struct('Fecha', {}, 'Max_W_m2', {}, 'Promedio_W_m2', {}, 'Energia_Wh_m2', {});
legend_entries = {};

% Fecha ficticia para alinear todos los gráficos en el mismo eje X
dummy_date = '2000-01-01';

% 4. Bucle de Procesamiento
for i = 1:num_files
    filename = file_list(i).name;
    full_path = fullfile(target_dir, filename);
    
    % Intentar extraer la fecha del nombre del archivo (YYYY_MM_DD)
    % Asume formato: YYYY_MM_DD_radiation.csv
    date_str_extracted = regexp(filename, '\d{4}_\d{2}_\d{2}', 'match', 'once');
    if isempty(date_str_extracted)
        date_str_extracted = ['Dia ', num2str(i)]; % Fallback si no tiene fecha
    else
        date_str_extracted = strrep(date_str_extracted, '_', '-');
    end
    
    % Leer datos
    opts = detectImportOptions(full_path);
    opts.VariableNamingRule = 'preserve';
    % Forzar lectura de todo como texto si falla la detección automática, para luego convertir
    % Pero primero probamos lectura estándar
    try
        data = readtable(full_path, opts);
    catch
        warning('Error leyendo formato de %s', filename);
        continue;
    end
    
    if isempty(data)
        warning('Archivo vacío: %s', filename);
        continue;
    end
    
    % Procesar tiempo y radiación
    raw_time = data{:, 1}; % Columna Time
    rad_vals = data{:, 2}; % Columna Radiation
    
    % --- CORRECCIÓN DE TIPO (FIX ERROR < 0) ---
    % Si rad_vals no es numérico (es cell o string), lo convertimos
    if ~isnumeric(rad_vals)
        rad_vals = str2double(string(rad_vals));
    end
    
    % Convertir cualquier NaN (texto no numérico) a 0 para evitar errores
    rad_vals(isnan(rad_vals)) = 0;
    
    % --- TRUCO DE ALINEACIÓN TEMPORAL ---
    % Creamos un datetime usando la fecha ficticia + la hora del archivo
    time_str = string(raw_time);
    full_datetime_str = dummy_date + " " + time_str;
    t = datetime(full_datetime_str, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
    
    % Filtrar datos ruidosos o negativos (opcional)
    rad_vals(rad_vals < 0) = 0;

    % --- CÁLCULO DE ESTADÍSTICAS ---
    val_max = max(rad_vals);
    val_mean = mean(rad_vals);
    
    % Calculo de Energía (Área bajo la curva) en Wh/m^2
    % Convertimos tiempo a horas fraccionales para integrar
    hours_vector = hour(t) + minute(t)/60 + second(t)/3600;
    % trapz integra y x. La unidad queda (W/m^2) * horas = Wh/m^2
    energy_wh = trapz(hours_vector, rad_vals);
    
    % Guardar stats
    stats_table(i).Fecha = date_str_extracted;
    stats_table(i).Max_W_m2 = val_max;
    stats_table(i).Promedio_W_m2 = val_mean;
    stats_table(i).Energia_Wh_m2 = energy_wh;
    
    % --- GRAFICAR ---
    plot(t, rad_vals, 'LineWidth', 1.5, 'Color', colors(i, :));
    
    % Crear entrada para la leyenda
    legend_entries{end+1} = sprintf('%s (Max: %.0f W/m^2)', date_str_extracted, val_max);
end

% 5. Formato Final del Gráfico
hold off;
title(['Comparativa de Radiación Solar - ', folder_name], 'Interpreter', 'none');
xlabel('Hora del día (Normalizada)');
ylabel('Radiación (W/m^2)');
grid on;
grid minor;

% Formato eje X
xtickformat('HH:mm');
xlim([datetime([dummy_date, ' 00:00:00']), datetime([dummy_date, ' 23:59:59'])]);

% Leyenda
lgd = legend(legend_entries, 'Location', 'bestoutside');
title(lgd, 'Fecha y Pico Máximo');

% 6. Imprimir Tabla de Resumen en Consola
fprintf('\n--- RESUMEN DE ESTADÍSTICAS SEMANALES ---\n');
T = struct2table(stats_table);
disp(T);

% Opcional: Calcular el día con mayor energía acumulada
if ~isempty(stats_table)
    [max_energy, idx] = max([stats_table.Energia_Wh_m2]);
    fprintf('El día con mayor generación de energía fue %s (%.2f Wh/m^2)\n', ...
        stats_table(idx).Fecha, max_energy);
end

% -------------------------------------------------------------------------
% 7. GUARDAR IMAGEN AUTOMÁTICAMENTE
% -------------------------------------------------------------------------
img_name = 'resumen_semanal_radiacion.png';
% Guardamos DENTRO de la carpeta de la semana (target_dir)
full_save_path = fullfile(target_dir, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end

% -------------------------------------------------------------------------
% 8. GENERAR REPORTE DE TEXTO (.txt)
% -------------------------------------------------------------------------
txt_name = 'resumen_semanal_radiacion.txt';
full_txt_path = fullfile(target_dir, txt_name);

fid = fopen(full_txt_path, 'w');
if fid == -1
    warning('No se pudo crear el archivo de texto.');
else
    fprintf(fid, '==========================================================\r\n');
    fprintf(fid, ' RESUMEN DE RADIACIÓN SEMANAL: %s\r\n', folder_name);
    fprintf(fid, '==========================================================\r\n\r\n');
    
    % Escribir día por día
    for k = 1:length(stats_table)
        s = stats_table(k);
        if ~isempty(s.Fecha)
            fprintf(fid, '[ %s ]\r\n', s.Fecha);
            fprintf(fid, '   Energía Total: %.2f Wh/m^2\r\n', s.Energia_Wh_m2);
            fprintf(fid, '   Pico Máximo:   %.2f W/m^2\r\n', s.Max_W_m2);
            fprintf(fid, '   Promedio:      %.2f W/m^2\r\n', s.Promedio_W_m2);
            fprintf(fid, '----------------------------------------------------------\r\n');
        end
    end
    
    % Resumen global (Hitos)
    if ~isempty(stats_table)
        [max_en, idx_best] = max([stats_table.Energia_Wh_m2]);
        [min_en, idx_worst] = min([stats_table.Energia_Wh_m2]);
        
        best_day = stats_table(idx_best);
        worst_day = stats_table(idx_worst);
        
        fprintf(fid, '\r\n>> HITOS DE LA SEMANA:\r\n');
        fprintf(fid, '🌞 Día con mayor generación: %s (%.2f Wh/m^2)\r\n', best_day.Fecha, max_en);
        fprintf(fid, '☁️ Día con menor generación: %s (%.2f Wh/m^2)\r\n', worst_day.Fecha, min_en);
    else
        fprintf(fid, '\r\n>> NO HAY DATOS SUFICIENTES PARA HITOS.\r\n');
    end
    
    fclose(fid);
    fprintf('Reporte de texto guardado en: %s\n', full_txt_path);
end