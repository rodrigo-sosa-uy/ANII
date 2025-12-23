% =========================================================================
% SCRIPT ESTANDARIZADO: TEMPERATURA CÁMARA
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN ---
target_date = '2025_12_22'; 

% 1. Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_temperature.csv'];
full_path = fullfile(script_path, filename);
fprintf('Procesando: %s\n', filename);

if ~isfile(full_path), error('Archivo no encontrado.'); end

% 2. Carga
opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve';
data = readtable(full_path, opts);

if isempty(data), warning('CSV vacío.'); return; end

raw_time = data{:, 1}; 
val_temp = data{:, 2}; 

% Filtro de Errores (-1.0)
valid_idx = val_temp > -50 & val_temp < 200;
t_clean = raw_time(valid_idx);
val_clean = val_temp(valid_idx);

% Tiempo
full_time_str = target_date + " " + string(t_clean);
t = datetime(full_time_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% 3. Gráfico
fig = figure('Name', 'Temp Cámara', 'Color', 'w', 'Position', [150, 100, 1000, 600]);
plot(t, val_clean, 'LineWidth', 2, 'Color', '#c0392b'); % Rojo
title(['Temp. Cámara - ', strrep(target_date, '_', '-')]);
ylabel('Temperatura (°C)');
xlabel('Hora');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);

% 4. Guardar Imagen
img_name = [target_date, '_analisis_temperatura_camara.png'];
saveas(fig, fullfile(script_path, img_name));
fprintf('Imagen guardada: %s\n', img_name);

% 5. Generar Reporte de Texto
max_t = max(val_clean);
min_t = min(val_clean);
avg_t = mean(val_clean);

txt_name = [target_date, '_resumen_temperatura_camara.txt'];
fid = fopen(fullfile(script_path, txt_name), 'w');

if fid ~= -1
    fprintf(fid, '========================================\r\n');
    fprintf(fid, ' RESUMEN CÁMARA TÉRMICA: %s\r\n', target_date);
    fprintf(fid, '========================================\r\n\r\n');
    fprintf(fid, '🔥 TEMPERATURA (°C):\r\n');
    fprintf(fid, '   Máxima:   %.2f\r\n', max_t);
    fprintf(fid, '   Mínima:   %.2f\r\n', min_t);
    fprintf(fid, '   Promedio: %.2f\r\n\r\n', avg_t);
    
    fprintf(fid, '⚙️ ESTADO DEL PROCESO:\r\n');
    if max_t > 90
        fprintf(fid, '   >> ALTA: Posible ebullición alcanzada.\r\n');
    elseif max_t > 50
        fprintf(fid, '   >> MEDIA: Calentamiento operativo.\r\n');
    else
        fprintf(fid, '   >> BAJA: Temperatura ambiente/inactivo.\r\n');
    end
    
    fprintf(fid, '   Lecturas Fallidas: %d\r\n', length(val_temp) - length(val_clean));
    fclose(fid);
    fprintf('Reporte guardado: %s\n', txt_name);
end