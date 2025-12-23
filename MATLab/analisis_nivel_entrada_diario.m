% =========================================================================
% SCRIPT DE ANÁLISIS DE NIVEL - TANQUE DE ENTRADA (FUSIÓN DE SENSORES)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
target_date = '2025_12_22'; 

% -------------------------------------------------------------------------
% 1. Configuración de Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_level_in.csv'];
full_path = fullfile(script_path, filename);

fprintf('Analizando nivel de entrada: %s\n', full_path);

if ~isfile(full_path)
    error('El archivo no existe en la carpeta actual: %s', filename);
end

% -------------------------------------------------------------------------
% 2. CARGA DE DATOS
% -------------------------------------------------------------------------
opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve';
try
    data = readtable(full_path, opts);
catch err
    error('Error leyendo el CSV. Revisa el formato.\nDetalle: %s', err.message);
end

if isempty(data)
    warning('El archivo CSV está vacío.');
    return;
end

% Asignación de variables
% Estructura: Time, Weight(kg), Distance(cm), Volume(ml)
raw_time = data{:, 1}; 
val_weight = data{:, 2};
val_dist   = data{:, 3};
val_vol    = data{:, 4};

% -------------------------------------------------------------------------
% 3. LIMPIEZA Y PREPARACIÓN
% -------------------------------------------------------------------------

% Convertir tiempo a datetime completo
full_time_str = target_date + " " + string(raw_time);
t = datetime(full_time_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% Límites del día completo
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% --- FILTRADO DE ERRORES DE SENSOR ---
% El Wemos envía -1.0 o -99.0 cuando hay error. Los filtramos para graficar.
% Creamos copias con NaNs para que el gráfico muestre "huecos" en lugar de líneas a cero.
plot_weight = val_weight; plot_weight(plot_weight < 0) = NaN;
plot_dist   = val_dist;   plot_dist(plot_dist < 0) = NaN;
plot_vol    = val_vol;    plot_vol(plot_vol < 0) = NaN;

% Fecha visual
date_display = strrep(target_date, '_', '-');

% -------------------------------------------------------------------------
% 4. GRAFICACIÓN (3 SUBPLOTS)
% -------------------------------------------------------------------------
fig = figure('Name', ['Nivel Entrada - ', target_date], 'Color', 'w', 'Position', [100, 50, 1000, 900]);

% --- SUBPLOT 1: PESO (Celda de Carga) ---
ax1 = subplot(3, 1, 1);
plot(t, plot_weight, 'LineWidth', 1.5, 'Color', '#8e44ad'); % Violeta
title(['Peso del Agua (Celda de Carga) - ', date_display]);
ylabel('Peso (kg)');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);
% Anotación Máximo
[max_w, idx_w] = max(plot_weight);
if ~isnan(max_w)
    text(t(idx_w), max_w, sprintf(' Max: %.2f kg', max_w), 'VerticalAlignment', 'bottom', 'BackgroundColor', 'w');
end

% --- SUBPLOT 2: DISTANCIA (Ultrasonido) ---
ax2 = subplot(3, 1, 2);
plot(t, plot_dist, 'LineWidth', 1.5, 'Color', '#e67e22'); % Naranja
title('Distancia al Nivel (Ultrasonido)');
ylabel('Distancia (cm)');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);
% Nota: En ultrasonido, el mínimo suele ser el nivel más alto (tanque lleno)
[min_d, idx_d] = min(plot_dist);
if ~isnan(min_d)
    text(t(idx_d), min_d, sprintf(' Min: %.1f cm (Nivel Alto)', min_d), 'VerticalAlignment', 'top', 'BackgroundColor', 'w');
end

% --- SUBPLOT 3: VOLUMEN (Fusión) ---
ax3 = subplot(3, 1, 3);
% Usamos 'area' para darle peso visual al volumen
area(t, plot_vol, 'FaceColor', '#3498db', 'FaceAlpha', 0.3, 'EdgeColor', '#2980b9', 'LineWidth', 1.5);
title('Volumen Estimado (Fusión de Sensores)');
ylabel('Volumen (ml)');
xlabel('Hora del día');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);

% Línea promedio
avg_vol = mean(plot_vol, 'omitnan');
if ~isnan(avg_vol)
    yline(avg_vol, '--', sprintf('Promedio: %.0f ml', avg_vol), ...
        'Color', '#2980b9', 'LabelHorizontalAlignment', 'right', 'LineWidth', 1.5);
end


% -------------------------------------------------------------------------
% 5. ANÁLISIS ESTADÍSTICO EN CONSOLA
% -------------------------------------------------------------------------
fprintf('\n========================================\n');
fprintf(' RESUMEN NIVEL ENTRADA: %s\n', target_date);
fprintf('========================================\n');

fprintf('⚖️  PESO (kg):\n');
fprintf('    Máximo: %.2f  |  Promedio: %.2f\n', max(plot_weight), mean(plot_weight, 'omitnan'));

fprintf('📏  DISTANCIA (cm):\n');
fprintf('    Mínima (Lleno): %.2f  |  Promedio: %.2f\n', min(plot_dist), mean(plot_dist, 'omitnan'));

fprintf('💧  VOLUMEN (ml):\n');
fprintf('    Máximo: %.0f  |  Promedio: %.0f\n', max(plot_vol), avg_vol);
fprintf('    Lecturas con Error: %d\n', sum(isnan(plot_vol)));
fprintf('========================================\n');

% -------------------------------------------------------------------------
% 6. GUARDADO AUTOMÁTICO DE IMAGEN
% -------------------------------------------------------------------------
img_name = [target_date, '_analisis_nivel_in.png'];
full_save_path = fullfile(script_path, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end

% -------------------------------------------------------------------------
% 7. GENERACIÓN DE REPORTE DE TEXTO (.txt)
% -------------------------------------------------------------------------
txt_name = [target_date, '_resumen_nivel_in.txt'];
full_txt_path = fullfile(script_path, txt_name);

fid = fopen(full_txt_path, 'w');
if fid ~= -1
    % Usamos \r\n para compatibilidad total
    fprintf(fid, '========================================\r\n');
    fprintf(fid, ' RESUMEN NIVEL ENTRADA: %s\r\n', target_date);
    fprintf(fid, '========================================\r\n\r\n');
    
    fprintf(fid, '⚖️ PESO (kg):\r\n');
    fprintf(fid, '   Máximo:   %.2f\r\n', max(plot_weight));
    fprintf(fid, '   Promedio: %.2f\r\n\r\n', mean(plot_weight, 'omitnan'));
    
    fprintf(fid, '📏 DISTANCIA (cm):\r\n');
    fprintf(fid, '   Mínimo (Más Lleno): %.2f\r\n', min(plot_dist));
    fprintf(fid, '   Promedio:           %.2f\r\n\r\n', mean(plot_dist, 'omitnan'));
    
    fprintf(fid, '💧 VOLUMEN (ml):\r\n');
    fprintf(fid, '   Máximo:   %.0f\r\n', max(plot_vol));
    fprintf(fid, '   Promedio: %.0f\r\n', avg_vol);
    fprintf(fid, '   Lecturas con Error: %d\r\n', sum(isnan(plot_vol)));
    
    fclose(fid);
    fprintf('Reporte de texto guardado: %s\n', full_txt_path);
else
    warning('No se pudo crear el archivo de texto.');
end