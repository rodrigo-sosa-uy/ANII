% =========================================================================
% SCRIPT DE ANÁLISIS METEOROLÓGICO DIARIO (OPENWEATHER)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Define la fecha a analizar
target_date = '2025_12_10'; 

% -------------------------------------------------------------------------

% 1. Construcción de ruta
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_weather.csv'];
full_path = fullfile(script_path, filename);

fprintf('Analizando archivo de clima: %s\n', full_path);

% 2. Verificación y Carga
if ~isfile(full_path)
    error('El archivo no existe en la carpeta actual: %s', filename);
end

opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve';
data = readtable(full_path, opts);

if isempty(data)
    warning('El archivo CSV está vacío.');
    return;
end

% 3. Procesamiento de Datos
% Estructura del CSV: Time, Condition, Description, Temp, Humidity, Clouds, Pressure
raw_time = data{:, 1};
cond_text = data{:, 2};
desc_text = data{:, 3};
temp_vals = data{:, 4};
hum_vals  = data{:, 5};
cloud_vals= data{:, 6};
pres_vals = data{:, 7};

% Crear vector de tiempo datetime
time_str = string(raw_time);
t = datetime(target_date + " " + time_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% --- DEFINICIÓN DE LÍMITES DE 24 HORAS (DUMMY TIME) ---
% Creamos el inicio y fin del día para forzar el eje X
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% -------------------------------------------------------------------------
% 4. GRÁFICO 1: METEOGRAMA (Evolución Temporal)
% -------------------------------------------------------------------------
% Se asegura fondo blanco (Tema Claro)
fig1 = figure('Name', ['Meteograma - ', target_date], 'Color', 'w', 'Position', [100, 100, 1000, 700]);

% --- SUBPLOT 1: Temperatura y Humedad ---
subplot(2, 1, 1);
yyaxis left
plot(t, temp_vals, 'LineWidth', 2, 'Color', '#D95319'); % Naranja
ylabel('Temperatura (°C)');
y_min = min(temp_vals) - 2;
y_max = max(temp_vals) + 2;
ylim([y_min, y_max]);

yyaxis right
plot(t, hum_vals, 'LineWidth', 1.5, 'Color', '#0072BD', 'LineStyle', '-'); % Azul
ylabel('Humedad Relativa (%)');
ylim([0 100]);

title(['Condiciones Termo-Higrométricas - ', strrep(target_date, '_', '-')]);
xlabel('Hora');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]); % <--- FORZAMOS EJE DE 24 HORAS
legend({'Temperatura', 'Humedad'}, 'Location', 'best');

% --- SUBPLOT 2: Nubosidad y Presión ---
subplot(2, 1, 2);
yyaxis left
area(t, cloud_vals, 'FaceColor', '#7E2F8E', 'FaceAlpha', 0.1, 'EdgeColor', '#7E2F8E'); % Violeta
ylabel('Cobertura Nubosa (%)');
ylim([0 100]);

yyaxis right
plot(t, pres_vals, 'LineWidth', 2, 'Color', '#77AC30'); % Verde
ylabel('Presión (hPa)');
% Ajustar escala de presión para ver variaciones pequeñas
if std(pres_vals) > 0
    ylim([min(pres_vals)-1, max(pres_vals)+1]);
end

title('Dinámica Atmosférica (Nubes y Presión)');
xlabel('Hora');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]); % <--- FORZAMOS EJE DE 24 HORAS
legend({'Nubosidad', 'Presión'}, 'Location', 'best');

% --- GUARDAR IMAGEN 1 ---
img_name1 = [target_date, '_analisis_clima_meteograma.png'];
full_save_path1 = fullfile(script_path, img_name1);
saveas(fig1, full_save_path1);
fprintf('Imagen guardada: %s\n', full_save_path1);

% -------------------------------------------------------------------------
% 5. GRÁFICO 2: DISTRIBUCIÓN DE CONDICIONES (Pie Chart)
% -------------------------------------------------------------------------
fig2 = figure('Name', 'Distribución del Clima', 'Color', 'w', 'Position', [1150, 100, 500, 400]);

% Convertir condiciones a categorías
cats = categorical(cond_text);
h = pie(cats);
title(['Condiciones Predominantes - ', strrep(target_date, '_', '-')]);

% --- GUARDAR IMAGEN 2 ---
img_name2 = [target_date, '_analisis_clima_distribucion.png'];
full_save_path2 = fullfile(script_path, img_name2);
saveas(fig2, full_save_path2);
fprintf('Imagen guardada: %s\n', full_save_path2);

% -------------------------------------------------------------------------
% 6. GENERACIÓN DE REPORTE DE TEXTO (.txt)
% -------------------------------------------------------------------------
% Preparar datos estadísticos
max_temp_val = max(temp_vals);
% BUG FIX: Usamos 'find' con '1' para obtener solo el primer índice
idx_max = find(temp_vals == max_temp_val, 1);
time_max_str = datestr(t(idx_max), 'HH:MM');

min_temp_val = min(temp_vals);
mean_temp_val = mean(temp_vals);
mean_hum_val = mean(hum_vals);
mean_cloud_val = mean(cloud_vals);
mean_pres_val = mean(pres_vals);

% Determinar estado del cielo
estado_cielo = 'Variable';
if mean_cloud_val < 20
    estado_cielo = 'Mayormente Despejado';
elseif mean_cloud_val > 70
    estado_cielo = 'Muy Nublado';
else
    estado_cielo = 'Parcialmente Nublado';
end

% Nombre del archivo de texto
txt_filename = [target_date, '_resumen_clima.txt'];
full_txt_path = fullfile(script_path, txt_filename);

% Escritura del archivo
fid = fopen(full_txt_path, 'w');
if fid == -1
    warning('No se pudo crear el archivo de texto.');
else
    % Usamos \r\n para compatibilidad total con Windows Notepad si fuera necesario
    fprintf(fid, '========================================\r\n');
    fprintf(fid, ' RESUMEN METEOROLÓGICO: %s\r\n', target_date);
    fprintf(fid, '========================================\r\n\r\n');
    
    fprintf(fid, '🌡️  TEMPERATURA:\r\n');
    fprintf(fid, '    Máxima:  %.2f °C (a las %s)\r\n', max_temp_val, time_max_str);
    fprintf(fid, '    Mínima:  %.2f °C\r\n', min_temp_val);
    fprintf(fid, '    Promedio: %.2f °C\r\n\r\n', mean_temp_val);
    
    fprintf(fid, '💧  HUMEDAD:\r\n');
    fprintf(fid, '    Promedio: %.2f %%\r\n', mean_hum_val);
    fprintf(fid, '    Rango:    %.0f%% - %.0f%%\r\n\r\n', min(hum_vals), max(hum_vals));
    
    fprintf(fid, '☁️  NUBOSIDAD:\r\n');
    fprintf(fid, '    Promedio: %.2f %%\r\n', mean_cloud_val);
    fprintf(fid, '    Estado:   %s\r\n\r\n', estado_cielo);
    
    fprintf(fid, '🌬️  PRESIÓN:\r\n');
    fprintf(fid, '    Promedio: %.2f hPa\r\n', mean_pres_val);
    
    fclose(fid);
    fprintf('Reporte de texto guardado: %s\n', full_txt_path);
end

% -------------------------------------------------------------------------
% 7. ANÁLISIS ESTADÍSTICO EN CONSOLA
% -------------------------------------------------------------------------
% (Opcional) Imprimimos también en consola para feedback inmediato
fprintf('\n========================================\n');
fprintf(' RESUMEN METEOROLÓGICO: %s\n', target_date);
fprintf('========================================\n');
fprintf('🌡️  TEMPERATURA: Máx %.2f °C (%s) | Prom %.2f °C\n', max_temp_val, time_max_str, mean_temp_val);
fprintf('💧  HUMEDAD:     Prom %.2f %%\n', mean_hum_val);
fprintf('☁️  NUBOSIDAD:   Prom %.2f %% (%s)\n', mean_cloud_val, estado_cielo);
fprintf('========================================\n');