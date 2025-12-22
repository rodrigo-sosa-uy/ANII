% =========================================================================
% SCRIPT DE ANÁLISIS DE CONTROL DIARIO (VÁLVULAS Y PROCESO)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Define la fecha a analizar
target_date = '2025_12_20'; 

% -------------------------------------------------------------------------
% 1. Configuración de Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

% Nombres de archivos esperados
file_in   = [target_date, '_control_in.csv'];
file_out  = [target_date, '_control_out.csv'];
file_proc = [target_date, '_control_process.csv'];

% Rutas completas
path_in   = fullfile(script_path, file_in);
path_out  = fullfile(script_path, file_out);
path_proc = fullfile(script_path, file_proc);

fprintf('Analizando control para la fecha: %s\n', target_date);

% --- DEFINICIÓN DE LÍMITES DE 24 HORAS ---
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% -------------------------------------------------------------------------
% 2. FUNCIÓN DE CARGA Y PREPROCESAMIENTO
% -------------------------------------------------------------------------
function [t_final, states_final] = cargar_datos_control(filepath, t_start, t_end)
    if ~isfile(filepath)
        % warning('Archivo no encontrado: %s', filepath); % Opcional
        t_final = [t_start, t_end];
        states_final = [0, 0]; % Asumimos apagado si no hay datos
        return;
    end

    opts = detectImportOptions(filepath);
    opts.VariableNamingRule = 'preserve';
    data = readtable(filepath, opts);

    if isempty(data)
        t_final = [t_start, t_end];
        states_final = [0, 0];
        return;
    end

    % Columnas esperadas: [Time, State]
    raw_time = data{:, 1};
    raw_state = data{:, 2};

    % Convertir tiempo
    [~, name, ~] = fileparts(filepath);
    date_part = name(1:10); % '2025_12_20'
    
    time_str = string(raw_time);
    t_events = datetime(date_part + " " + time_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

    % --- TRUCO PARA GRÁFICA CUADRADA PERFECTA ---
    % Agregamos puntos al inicio y fin del día para completar la gráfica
    
    % 1. Punto inicial (00:00)
    if t_events(1) > t_start
        t_final = [t_start; t_events];
        % Asumimos estado 0 (OFF) al inicio del día antes del primer evento
        states_final = [0; raw_state]; 
    else
        t_final = t_events;
        states_final = raw_state;
    end
    
    % 2. Punto final (23:59)
    if t_final(end) < t_end
        t_final = [t_final; t_end];
        states_final = [states_final; states_final(end)];
    end
end

% -------------------------------------------------------------------------
% 3. CARGA DE DATOS
% -------------------------------------------------------------------------
[t_in, s_in] = cargar_datos_control(path_in, t_start, t_end);
[t_out, s_out] = cargar_datos_control(path_out, t_start, t_end);
[t_proc, s_proc] = cargar_datos_control(path_proc, t_start, t_end);

% -------------------------------------------------------------------------
% 4. GRAFICACIÓN
% -------------------------------------------------------------------------
fig = figure('Name', ['Análisis de Actuadores - ', target_date], 'Color', 'w', 'Position', [100, 50, 1000, 900]);

% --- SUBPLOT 1: VÁLVULA DE ENTRADA ---
subplot(3, 1, 1);
stairs(t_in, s_in, 'LineWidth', 2, 'Color', '#3498db'); % Azul
title('Válvula de Entrada (Llenado)');
ylabel('Estado');
yticks([0 1]);
yticklabels({'CERRADA', 'ABIERTA'});
ylim([-0.2 1.2]); % Margen visual
grid on; grid minor;
xlim([t_start, t_end]);
xtickformat('HH:mm');

% Calcular tiempo total activo
durations_in = diff(datenum(t_in)) * 24 * 60; % Minutos
total_on_in = sum(durations_in(s_in(1:end-1) == 1));
text(t_start + minutes(30), 0.8, sprintf('Tiempo Activo: %.1f min', total_on_in), 'FontSize', 10, 'BackgroundColor', 'w', 'EdgeColor', 'k');


% --- SUBPLOT 2: VÁLVULA DE SALIDA ---
subplot(3, 1, 2);
stairs(t_out, s_out, 'LineWidth', 2, 'Color', '#e74c3c'); % Rojo
title('Válvula de Salida (Drenaje)');
ylabel('Estado');
yticks([0 1]);
yticklabels({'CERRADA', 'ABIERTA'});
ylim([-0.2 1.2]);
grid on; grid minor;
xlim([t_start, t_end]);
xtickformat('HH:mm');

durations_out = diff(datenum(t_out)) * 24 * 60;
total_on_out = sum(durations_out(s_out(1:end-1) == 1));
text(t_start + minutes(30), 0.8, sprintf('Tiempo Activo: %.1f min', total_on_out), 'FontSize', 10, 'BackgroundColor', 'w', 'EdgeColor', 'k');


% --- SUBPLOT 3: PROCESO GENERAL ---
subplot(3, 1, 3);
% CORRECCIÓN: Usamos stairs para que se vea rectangular (PWM) igual que las válvulas
stairs(t_proc, s_proc, 'LineWidth', 2, 'Color', '#2ecc71'); % Verde
title('Estado del Proceso General');
ylabel('Estado');
yticks([0 1]);
yticklabels({'STOP', 'START'});
ylim([-0.2 1.2]);
grid on; grid minor;
xlim([t_start, t_end]);
xtickformat('HH:mm');
xlabel('Hora del día');

durations_proc = diff(datenum(t_proc)) * 24 * 60;
total_on_proc = sum(durations_proc(s_proc(1:end-1) == 1));
text(t_start + minutes(30), 0.8, sprintf('Duración Total: %.1f min', total_on_proc), 'FontSize', 10, 'BackgroundColor', 'w', 'EdgeColor', 'k');


% -------------------------------------------------------------------------
% 5. GUARDADO AUTOMÁTICO
% -------------------------------------------------------------------------
img_name = [target_date, '_analisis_control.png'];
full_save_path = fullfile(script_path, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end

% -------------------------------------------------------------------------
% 6. RESUMEN EN CONSOLA
% -------------------------------------------------------------------------
fprintf('\n=== RESUMEN DE TIEMPOS DE ACTIVIDAD ===\n');
fprintf('Válvula Entrada: %.2f minutos\n', total_on_in);
fprintf('Válvula Salida:  %.2f minutos\n', total_on_out);
fprintf('Proceso Activo:  %.2f minutos\n', total_on_proc);
fprintf('=======================================\n');