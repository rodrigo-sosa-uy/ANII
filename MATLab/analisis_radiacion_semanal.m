% =========================================================================
% SCRIPT PARA COMPARAR RADIACIÓN DE VARIOS DÍAS (SEMANA)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Nombre de la carpeta que contiene los archivos de la semana.
% Debe estar EN LA MISMA CARPETA que este script.
folder_name = 'semana_2025_11_25';

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
figure('Name', 'Comparativa Semanal de Radiación', 'Color', 'w', 'Position', [100, 100, 1000, 600]);
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
    data = readtable(full_path, opts);

    if isempty(data)
        warning('Archivo vacío: %s', filename);
        continue;
    end

    % Procesar tiempo y radiación
    raw_time = data{:, 1}; % Columna Time
    rad_vals = data{:, 2}; % Columna Radiation

    % --- TRUCO DE ALINEACIÓN TEMPORAL ---
    % Creamos un datetime usando la fecha ficticia + la hora del archivo
    % Así todas las curvas se grafican sobre el "mismo día"
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
[max_energy, idx] = max([stats_table.Energia_Wh_m2]);
fprintf('El día con mayor generación de energía fue %s (%.2f Wh/m^2)\n', ...
    stats_table(idx).Fecha, max_energy);
