% =========================================================================
% SCRIPT DE ANÁLISIS SEMANAL: RADIACIÓN + CLIMA (LEYENDAS SEPARADAS)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Nombre de la carpeta que contiene los archivos (radiación y clima)
folder_name = '2025_12_08 to 2025_12_14';

% -------------------------------------------------------------------------

% 1. Configuración de Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

target_dir = fullfile(script_path, folder_name);
fprintf('Buscando archivos en: %s\n', target_dir);

% 2. Obtener lista de archivos de RADIACIÓN
if ~isfolder(target_dir)
    error('La carpeta "%s" no existe.', folder_name);
end

% Buscamos solo los de radiación para iterar sobre ellos
file_list = dir(fullfile(target_dir, '*_radiation.csv'));
num_files = length(file_list);

if num_files == 0
    error('No se encontraron archivos _radiation.csv en la carpeta.');
end

fprintf('Se encontraron %d días para procesar.\n', num_files);

% 3. Preparar Gráfico
% Guardamos el handle en 'fig' para guardar después
fig = figure('Name', 'Comparativa Semanal: Radiación y Clima', 'Color', 'w', 'Position', [100, 50, 1200, 800]);

% Paleta de colores consistente para ambos gráficos
colors = turbo(num_files);

% Estructura extendida para estadísticas
stats_table = struct('Fecha', {}, ...
                     'Max_Rad_W_m2', {}, ...
                     'Energia_Wh_m2', {}, ...
                     'Nubosidad_Media_Pct', {}, ...
                     'Temp_Max_C', {}, ...
                     'Condicion_Clima', {});

% Listas separadas para las leyendas
legend_entries_rad = {};
legend_entries_cloud = {};

dummy_date = '2000-01-01'; % Para alinear eje X

% Preparamos los subplots
ax1 = subplot(2, 1, 1); hold on;
ax2 = subplot(2, 1, 2); hold on;

% 4. Bucle de Procesamiento
for i = 1:num_files
    % --- A. PROCESAR RADIACIÓN ---
    filename_rad = file_list(i).name;
    full_path_rad = fullfile(target_dir, filename_rad);
    
    % Extraer fecha del nombre
    date_str = regexp(filename_rad, '\d{4}_\d{2}_\d{2}', 'match', 'once');
    if isempty(date_str)
        date_display = ['Dia ', num2str(i)];
    else
        date_display = strrep(date_str, '_', '-');
    end
    
    % Leer Radiación
    opts = detectImportOptions(full_path_rad);
    opts.VariableNamingRule = 'preserve';
    data_rad = readtable(full_path_rad, opts);
    
    if isempty(data_rad)
        warning('Archivo vacío: %s', filename_rad);
        continue;
    end
    
    raw_time = data_rad{:, 1}; 
    rad_vals = data_rad{:, 2}; 
    
    % Alineación temporal
    time_str = string(raw_time);
    t = datetime(dummy_date + " " + time_str, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
    rad_vals(rad_vals < 0) = 0; 
    
    % Estadísticas Radiación
    val_max = max(rad_vals);
    hours_vec = hour(t) + minute(t)/60 + second(t)/3600;
    energy_wh = trapz(hours_vec, rad_vals);
    
    % GRAFICAR RADIACIÓN (Arriba)
    plot(ax1, t, rad_vals, 'LineWidth', 1.5, 'Color', colors(i, :));
    
    % --- B. PROCESAR CLIMA (OPENWEATHER) ---
    filename_weather = strrep(filename_rad, 'radiation', 'weather');
    full_path_weather = fullfile(target_dir, filename_weather);
    
    avg_clouds = NaN;
    max_temp = NaN;
    main_cond = 'N/A';
    has_valid_weather = false; % Bandera para saber si graficamos datos reales
    
    if isfile(full_path_weather)
        try
            opts_w = detectImportOptions(full_path_weather);
            opts_w.VariableNamingRule = 'preserve';
            data_w = readtable(full_path_weather, opts_w);
            
            if ~isempty(data_w)
                raw_time_w = data_w{:, 1};
                conds = data_w{:, 2};
                temps = data_w{:, 4};
                clouds = data_w{:, 6};
                
                time_str_w = string(raw_time_w);
                t_w = datetime(dummy_date + " " + time_str_w, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');

                avg_clouds = mean(clouds);
                max_temp = max(temps);
                main_cond = char(mode(categorical(conds))); 
                
                has_valid_weather = true;
            end
        catch
            warning('Error procesando clima: %s', filename_weather);
        end
    end
    
    % GRAFICAR NUBES (Abajo)
    if has_valid_weather
        % Si hay datos, graficamos la curva real
        plot(ax2, t_w, clouds, 'LineWidth', 1.5, 'Color', colors(i, :));
    else
        % --- FIX: SI NO HAY DATOS, GRAFICAR LÍNEA INVISIBLE (NaN) ---
        % Esto mantiene el contador de objetos sincronizado con la leyenda
        plot(ax2, t, nan(size(t)), 'LineWidth', 1.5, 'Color', colors(i, :));
    end
    
    % --- C. GUARDAR ESTADÍSTICAS Y LEYENDAS ---
    stats_table(i).Fecha = date_display;
    stats_table(i).Max_Rad_W_m2 = val_max;
    stats_table(i).Energia_Wh_m2 = energy_wh;
    stats_table(i).Nubosidad_Media_Pct = avg_clouds;
    stats_table(i).Temp_Max_C = max_temp;
    stats_table(i).Condicion_Clima = main_cond;
    
    % Crear leyenda para Radiación (Solo Energía)
    legend_entries_rad{end+1} = sprintf('%s (E: %.0f Wh)', date_display, energy_wh);
    
    % Crear leyenda para Clima (Nubes y Condición)
    if isnan(avg_clouds)
        legend_entries_cloud{end+1} = sprintf('%s (Sin Datos)', date_display);
    else
        legend_entries_cloud{end+1} = sprintf('%s (%.0f%% | %s)', date_display, avg_clouds, main_cond);
    end
    
end

% 5. Formato Final de Gráficos

% --- SUBPLOT 1: RADIACIÓN ---
axes(ax1); 
title(['Análisis Semanal: Radiación Solar - ', folder_name], 'Interpreter', 'none');
ylabel('Radiación (W/m^2)');
grid on; grid minor;
xtickformat('HH:mm');
xlim([datetime([dummy_date, ' 00:00:00']), datetime([dummy_date, ' 23:59:59'])]);

% LEYENDA SUPERIOR (Energía)
lgd1 = legend(ax1, legend_entries_rad, 'Location', 'eastoutside');
title(lgd1, 'Fecha (Energía Total)');

% --- SUBPLOT 2: NUBES ---
axes(ax2); 
title('Perfil de Nubosidad (%)');
ylabel('Cobertura Nubosa (%)');
xlabel('Hora del día (Sincronizada)');
ylim([-5 105]); 
grid on; grid minor;
xtickformat('HH:mm');
xlim([datetime([dummy_date, ' 00:00:00']), datetime([dummy_date, ' 23:59:59'])]);

% LEYENDA INFERIOR (Clima)
lgd2 = legend(ax2, legend_entries_cloud, 'Location', 'eastoutside');
title(lgd2, 'Fecha (Nubes Media | Clima)');

% 6. Imprimir Tabla de Resumen
fprintf('\n====================================================================\n');
fprintf('                 RESUMEN SEMANAL INTEGRADO\n');
fprintf('====================================================================\n');

T = struct2table(stats_table);
disp(T);

fprintf('\n--- Conclusiones Automáticas ---\n');
[max_en, idx_best] = max([stats_table.Energia_Wh_m2]);
[min_en, idx_worst] = min([stats_table.Energia_Wh_m2]);

best_day = stats_table(idx_best);
worst_day = stats_table(idx_worst);

fprintf('🌞 MEJOR DÍA: %s (%.2f Wh/m^2, Nubes: %.1f%%)\n', best_day.Fecha, best_day.Energia_Wh_m2, best_day.Nubosidad_Media_Pct);
fprintf('☁️ PEOR DÍA:  %s (%.2f Wh/m^2, Nubes: %.1f%%)\n', worst_day.Fecha, worst_day.Energia_Wh_m2, worst_day.Nubosidad_Media_Pct);
fprintf('====================================================================\n');

% -------------------------------------------------------------------------
% 7. GUARDAR IMAGEN AUTOMÁTICAMENTE
% -------------------------------------------------------------------------
img_name = 'resumen_semanal_clima_rad.png';
full_save_path = fullfile(target_dir, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end