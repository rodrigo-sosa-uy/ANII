% =========================================================================
% SCRIPT DE ANÁLISIS IOT: RADIACIÓN VS CLIMA (OPENWEATHER)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Define la fecha a analizar (Formato: YYYY_MM_DD)
target_date = '2025_12_10'; % Asegúrate que coincida con tus archivos

% -------------------------------------------------------------------------

% 1. Construcción de rutas dinámicas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

file_rad = [target_date, '_radiation.csv'];
file_weather = [target_date, '_weather.csv'];

path_rad = fullfile(script_path, file_rad);
path_weather = fullfile(script_path, file_weather);

fprintf('Analizando fecha: %s\n', target_date);

% -------------------------------------------------------------------------
% 2. CARGA DE DATOS DE RADIACIÓN
% -------------------------------------------------------------------------
if ~isfile(path_rad)
    error('No se encontró el archivo de radiación: %s', file_rad);
end

opts_rad = detectImportOptions(path_rad);
opts_rad.VariableNamingRule = 'preserve';
data_rad = readtable(path_rad, opts_rad);

if isempty(data_rad)
    warning('El archivo de radiación está vacío.');
    return;
end

% Procesar tiempo Radiación
raw_time_rad = data_rad{:, 1}; 
rad_vals = data_rad{:, 2}; 

time_str_rad = string(raw_time_rad);
dt_rad = datetime(target_date + " " + time_str_rad, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% -------------------------------------------------------------------------
% 3. CARGA DE DATOS DE CLIMA (Opcional pero recomendado)
% -------------------------------------------------------------------------
has_weather = false;
if isfile(path_weather)
    fprintf('Archivo de clima encontrado. Cruzando datos...\n');
    opts_weath = detectImportOptions(path_weather);
    opts_weath.VariableNamingRule = 'preserve';
    data_weath = readtable(path_weather, opts_weath);
    
    if ~isempty(data_weath)
        has_weather = true;
        % Estructura esperada: Time, Condition, Desc, Temp, Hum, Clouds, Pressure
        % Usamos índices para evitar problemas con nombres largos
        raw_time_weath = data_weath{:, 1};
        weath_cond = data_weath{:, 2};     % Texto (ej. Clear)
        weath_temp = data_weath{:, 4};     % Temperatura
        weath_clouds = data_weath{:, 6};   % Nubes %
        
        time_str_weath = string(raw_time_weath);
        dt_weath = datetime(target_date + " " + time_str_weath, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
    end
else
    warning('No se encontró archivo de clima (%s). Se graficará solo radiación.', file_weather);
end

% -------------------------------------------------------------------------
% 4. GRAFICACIÓN (PANEL DOBLE)
% -------------------------------------------------------------------------
if has_weather
    % Guardamos el handle de la figura en 'fig' para poder guardarla después
    fig = figure('Name', ['Análisis Cruzado: ', target_date], 'Color', 'w', 'Position', [100, 100, 1000, 800]);
    
    % --- SUBPLOT 1: RADIACIÓN ---
    subplot(2, 1, 1);
    plot(dt_rad, rad_vals, 'LineWidth', 1.5, 'Color', '#D95319'); % Naranja
    title(['Radiación Solar - ', strrep(target_date, '_', '-')]);
    ylabel('Irradiancia (W/m^2)');
    grid on; grid minor;
    xtickformat('HH:mm');
    xlim([min(dt_rad), max(dt_rad)]);
    
    % Estadísticas en gráfico 1
    max_rad = max(rad_vals);
    mean_rad = mean(rad_vals);
    legend({sprintf('Max: %.1f W/m^2', max_rad)}, 'Location', 'northwest');

    % --- SUBPLOT 2: CLIMA (NUBES Y TEMP) ---
    subplot(2, 1, 2);
    
    % Eje Izquierdo: Nubes (Barra o Area)
    yyaxis left
    b = bar(dt_weath, weath_clouds, 0.4, 'FaceColor', '#0072BD', 'FaceAlpha', 0.6);
    ylabel('Cobertura Nubosa (%)');
    ylim([0 100]);
    
    % Eje Derecho: Temperatura
    yyaxis right
    plot(dt_weath, weath_temp, 'o-', 'LineWidth', 2, 'Color', '#77AC30', 'MarkerFaceColor', 'w');
    ylabel('Temperatura (°C)');
    
    title('Condiciones Meteorológicas (OpenWeatherMap)');
    xlabel('Hora del día');
    grid on;
    xtickformat('HH:mm');
    xlim([min(dt_rad), max(dt_rad)]); % Sincronizar eje X con radiación
    
    legend({'Nubes (%)', 'Temp (°C)'}, 'Location', 'northwest');
    
else
    % --- MODO SOLO RADIACIÓN (FALLBACK) ---
    fig = figure('Name', 'Análisis de Radiación Solar', 'Color', 'w');
    plot(dt_rad, rad_vals, 'LineWidth', 1.5, 'Color', '#D95319');
    title(['Perfil de Radiación Solar - ', strrep(target_date, '_', '-')]);
    xlabel('Hora del día');
    ylabel('Radiación (W/m^2)');
    grid on; grid minor;
    xtickformat('HH:mm');
    
    max_rad = max(rad_vals);
    mean_rad = mean(rad_vals);
end

% -------------------------------------------------------------------------
% 5. ANÁLISIS ESTADÍSTICO EN CONSOLA
% -------------------------------------------------------------------------
fprintf('\n--- RESUMEN DEL DÍA ---\n');
fprintf('Radiación Pico:    %.2f W/m^2\n', max_rad);
fprintf('Radiación Media:   %.2f W/m^2\n', mean_rad);

if has_weather
    mean_clouds = mean(weath_clouds);
    max_temp = max(weath_temp);
    
    fprintf('Nubosidad Media:   %.1f %%\n', mean_clouds);
    fprintf('Temperatura Máx:   %.1f °C\n', max_temp);
    
    % Análisis de correlación simple
    if mean_clouds > 50 && mean_rad > 800
        fprintf('>> OBSERVACIÓN: Día nublado pero con alta radiación (¿Nubes dispersas/Reflejo?)\n');
    elif mean_clouds > 80 && mean_rad < 300
        fprintf('>> OBSERVACIÓN: Baja radiación consistente con día muy nublado.\n');
    elif mean_clouds < 20 && mean_rad > 800
        fprintf('>> OBSERVACIÓN: Comportamiento esperado de cielo despejado.\n');
    end
    
    % Mostrar condiciones predominantes
    conditions = categorical(weath_cond);
    most_common = mode(conditions);
    fprintf('Clima Predominante: %s\n', char(most_common));
end
fprintf('-----------------------\n');

% -------------------------------------------------------------------------
% 6. GUARDAR IMAGEN AUTOMÁTICAMENTE
% -------------------------------------------------------------------------
img_name = [target_date, '_analisis_rad_clima.png'];
full_save_path = fullfile(script_path, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end