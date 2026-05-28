/**
 * B24 — Mon Planning InovaYa
 * Tableau de bord individuel du collaborateur connecté.
 * Page Frappe native — 0 dépendance externe, responsive.
 *
 * Affiche :
 *   - Tâches projet assignées (avec heures allouées / réalisées, Eisenhower, échéance)
 *   - Tâches annexes (sans projet)
 *   - Filtres : Tout / En retard / Conflit absence
 *   - Mise à jour statut inline
 *   - Bouton "Saisir du temps" → nouvelle Timesheet pré-remplie
 */

frappe.pages['mon-planning-inovaya'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Mon Planning',
		single_column: true,
	});

	page.add_action_icon('refresh', function () {
		_mp_refresh(page);
	});

	// Filtre actif ('all' | 'late' | 'conflit')
	page._mp_filter = 'all';

	_mp_refresh(page);
};

/* ── Appel API ───────────────────────────────────────────────────────────── */

function _mp_refresh(page) {
	frappe.call({
		method: 'inovaya_gdp.inovaya.page.mon_planning_inovaya.mon_planning_inovaya.get_my_tasks',
		freeze: true,
		freeze_message: 'Chargement de vos tâches…',
		callback: function (r) {
			if (r.message) {
				page._mp_data = r.message;
				_mp_render(page, r.message);
			}
		},
	});
}

/* ── Rendu principal ────────────────────────────────────────────────────── */

function _mp_render(page, data) {
	var $body = $(page.body);
	$body.empty();

	var tasks        = data.tasks        || [];
	var annexe_tasks = data.annexe_tasks || [];
	var statuses     = data.statuses     || [];

	/* ── Filtres ── */
	var $filters = $('<div class="mp-filters" style="display:flex;gap:8px;'
		+ 'margin-bottom:16px;flex-wrap:wrap;"></div>');

	var filter_defs = [
		{ key: 'all',    label: 'Toutes les tâches (' + tasks.length + ')' },
		{ key: 'late',   label: '⚠ En retard (' + tasks.filter(function(t){return t.is_late;}).length + ')' },
		{ key: 'conflit',label: '🔴 Conflit absence (' + tasks.filter(function(t){return t.conflit_absence;}).length + ')' },
	];
	filter_defs.forEach(function (fd) {
		var is_active = page._mp_filter === fd.key;
		var $btn = $('<button class="btn btn-sm '
			+ (is_active ? 'btn-primary' : 'btn-default')
			+ '" data-filter="' + fd.key + '">'
			+ fd.label + '</button>');
		$filters.append($btn);
	});
	$body.append($filters);

	/* Filtre clic */
	$body.on('click', '.mp-filters button', function () {
		page._mp_filter = $(this).data('filter');
		_mp_render(page, page._mp_data);
	});

	/* ── Appliquer filtre ── */
	var visible_tasks = tasks.filter(function (t) {
		if (page._mp_filter === 'late')    return t.is_late;
		if (page._mp_filter === 'conflit') return t.conflit_absence;
		return true;
	});

	/* ── Tableau Tâches Projet ── */
	$body.append('<h6 style="margin-bottom:8px;color:#555;">Tâches projet</h6>');

	if (!visible_tasks.length) {
		$body.append('<div class="text-muted" style="margin-bottom:20px;">'
			+ 'Aucune tâche correspondant au filtre.</div>');
	} else {
		$body.append(_mp_build_task_table(visible_tasks, statuses));
	}

	/* ── Tableau Annexes Tasks ── */
	if (annexe_tasks.length && page._mp_filter === 'all') {
		$body.append('<h6 style="margin:20px 0 8px;color:#555;">Tâches annexes (hors projet)</h6>');
		$body.append(_mp_build_annexe_table(annexe_tasks));
	}

	/* ── Événements status dropdown ── */
	$body.on('change', '.mp-status-select', function () {
		var $sel      = $(this);
		var task_name = $sel.data('task');
		var new_status = $sel.val();

		frappe.call({
			method: 'inovaya_gdp.inovaya.page.mon_planning_inovaya.mon_planning_inovaya.update_task_status',
			args: { task_name: task_name, new_status: new_status },
			callback: function (r) {
				if (r.message && r.message.ok) {
					frappe.show_alert({
						message: 'Statut mis à jour : ' + new_status,
						indicator: 'green',
					}, 3);
					// Actualiser si tâche devient Completed/Cancelled (disparaît de la liste)
					if (['Completed', 'Cancelled'].includes(new_status)) {
						setTimeout(function () { _mp_refresh(page); }, 800);
					}
				}
			},
		});
	});

	/* ── Bouton Timesheet ── */
	$body.on('click', '.mp-ts-btn', function () {
		var task_name    = $(this).data('task');
		var project_name = $(this).data('project');
		// Ouvrir nouvelle Timesheet en pré-remplissant le projet/tâche via URL
		var url = '/app/timesheet/new-timesheet-1?parent_project='
			+ encodeURIComponent(project_name || '');
		// En v16, frappe.set_route est plus propre
		frappe.set_route('Form', 'Timesheet', 'new-timesheet-1');
	});
}

/* ── Construction tableau tâches projet ─────────────────────────────────── */

function _mp_build_task_table(tasks, statuses) {
	var header =
		'<thead><tr>'
		+ '<th>Projet</th>'
		+ '<th>Tâche</th>'
		+ '<th style="min-width:130px;">Statut</th>'
		+ '<th>Eisenhower</th>'
		+ '<th style="text-align:right;">Alloué</th>'
		+ '<th style="text-align:right;">Réalisé</th>'
		+ '<th style="text-align:center;">Échéance</th>'
		+ '<th style="text-align:center;"></th>'
		+ '</tr></thead>';

	var rows = tasks.map(function (t) {
		var row_style = '';
		if (t.conflit_absence) {
			row_style = 'background:#fff3e0;';
		} else if (t.is_late) {
			row_style = 'background:#fdecea;';
		}

		var late_badge = t.is_late
			? '<span style="background:#dc3545;color:#fff;padding:1px 5px;'
				+ 'border-radius:3px;font-size:11px;margin-left:4px;">RETARD</span>'
			: '';
		var conflit_badge = t.conflit_absence
			? '<span style="background:#ff9800;color:#fff;padding:1px 5px;'
				+ 'border-radius:3px;font-size:11px;margin-left:4px;">ABS.</span>'
			: '';

		var status_select = '<select class="form-control form-control-sm mp-status-select"'
			+ ' data-task="' + frappe.utils.escape_html(t.name) + '">'
			+ statuses.map(function (s) {
				return '<option value="' + s + '"'
					+ (s === t.status ? ' selected' : '') + '>' + s + '</option>';
			}).join('')
			+ '</select>';

		var ts_btn = '<button class="btn btn-xs btn-default mp-ts-btn" '
			+ 'data-task="' + frappe.utils.escape_html(t.name) + '" '
			+ 'data-project="' + frappe.utils.escape_html(t.project) + '" '
			+ 'title="Saisir du temps">⏱</button>';

		return '<tr style="' + row_style + '">'
			+ '<td><a href="/app/project/' + encodeURIComponent(t.project) + '">'
				+ frappe.utils.escape_html(t.project || '—') + '</a></td>'
			+ '<td><a href="/app/task/' + encodeURIComponent(t.name) + '">'
				+ frappe.utils.escape_html(t.subject)
				+ '</a>' + late_badge + conflit_badge + '</td>'
			+ '<td>' + status_select + '</td>'
			+ '<td style="font-size:12px;color:#666;">'
				+ frappe.utils.escape_html(t.eisenhower || '—') + '</td>'
			+ '<td style="text-align:right;">' + (t.allocated_hours || 0).toFixed(1) + 'h</td>'
			+ '<td style="text-align:right;">' + (t.actual_hours    || 0).toFixed(1) + 'h</td>'
			+ '<td style="text-align:center;white-space:nowrap;font-size:12px;">'
				+ (t.exp_end_date
					? frappe.datetime.str_to_user(t.exp_end_date)
					: '—') + '</td>'
			+ '<td style="text-align:center;">' + ts_btn + '</td>'
			+ '</tr>';
	}).join('');

	return $('<div style="overflow-x:auto;">'
		+ '<table class="table table-bordered table-sm mp-task-table">'
		+ header
		+ '<tbody>' + rows + '</tbody>'
		+ '</table></div>');
}

/* ── Construction tableau annexes ───────────────────────────────────────── */

function _mp_build_annexe_table(annexe_tasks) {
	var header =
		'<thead><tr>'
		+ '<th>Tâche annexe</th>'
		+ '<th style="min-width:130px;">Statut</th>'
		+ '<th style="text-align:center;">Échéance</th>'
		+ '</tr></thead>';

	var rows = annexe_tasks.map(function (at) {
		var row_style = at.is_late ? 'background:#fdecea;' : '';
		var late_badge = at.is_late
			? '<span style="background:#dc3545;color:#fff;padding:1px 5px;'
				+ 'border-radius:3px;font-size:11px;margin-left:4px;">RETARD</span>'
			: '';

		return '<tr style="' + row_style + '">'
			+ '<td><a href="/app/annexe-task/' + encodeURIComponent(at.name) + '">'
				+ frappe.utils.escape_html(at.subject || at.name)
				+ '</a>' + late_badge + '</td>'
			+ '<td>' + frappe.utils.escape_html(at.status || '—') + '</td>'
			+ '<td style="text-align:center;font-size:12px;">'
				+ (at.exp_end_date
					? frappe.datetime.str_to_user(at.exp_end_date)
					: '—') + '</td>'
			+ '</tr>';
	}).join('');

	return $('<div style="overflow-x:auto;">'
		+ '<table class="table table-bordered table-sm">'
		+ header
		+ '<tbody>' + rows + '</tbody>'
		+ '</table></div>');
}
