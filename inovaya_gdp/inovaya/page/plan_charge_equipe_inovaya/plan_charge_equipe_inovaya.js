/**
 * B25 — Plan de Charge Équipe InovaYa
 * Page Frappe native — 0 dépendance externe.
 *
 * Vue : 4 semaines (S-1/S/S+1/S+2) × collaborateurs
 * Couleurs : vert < 80% | orange 80-100% | rouge > 100%
 * Clic sur cellule → liste des tâches de la semaine
 * Navigation semaine précédente / suivante
 * Bouton "Ajouter tâche annexe" → frappe.new_doc('Annexe Task')
 */

frappe.pages['plan-charge-equipe-inovaya'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Plan de Charge Équipe',
		single_column: true,
	});

	// Bouton rafraîchir dans la barre d'actions
	page.add_action_icon('refresh', function () {
		_pce_refresh(page);
	});

	// État global de la page
	page._pce_from_monday = _pce_current_monday();

	// Premier chargement
	_pce_refresh(page);
};

/* ── Helpers date ────────────────────────────────────────────────────────── */

function _pce_current_monday() {
	var d = frappe.datetime.str_to_obj(frappe.datetime.nowdate());
	var day = d.getDay();
	var diff = (day === 0) ? -6 : 1 - day;   // reculer au lundi
	d.setDate(d.getDate() + diff);
	return frappe.datetime.obj_to_str(d);
}

function _pce_shift_week(from_monday_str, offset_weeks) {
	var d = frappe.datetime.str_to_obj(from_monday_str);
	d.setDate(d.getDate() + offset_weeks * 7);
	return frappe.datetime.obj_to_str(d);
}

/* ── Appel API ───────────────────────────────────────────────────────────── */

function _pce_refresh(page) {
	frappe.call({
		method: 'inovaya_gdp.inovaya.page.plan_charge_equipe_inovaya.plan_charge_equipe_inovaya.get_charge_data',
		args: { from_monday: page._pce_from_monday },
		freeze: true,
		freeze_message: 'Chargement du plan de charge…',
		callback: function (r) {
			if (r.message) {
				_pce_render(page, r.message);
			}
		},
	});
}

/* ── Rendu ───────────────────────────────────────────────────────────────── */

function _pce_render(page, data) {
	var $body = $(page.body);
	$body.empty();

	var weeks     = data.weeks;      // [{start,end,label}, ...]
	var employees = data.employees;  // [{email,name,weeks:{wlabel:{hours,pct,tasks}}}]
	var capacity  = data.capacity;

	/* ── Barre de navigation ── */
	var cur_label = weeks[1] ? weeks[1].label : '';
	var $nav = $('<div class="pce-nav" style="display:flex;align-items:center;gap:12px;'
		+ 'padding:12px 0 16px 0;flex-wrap:wrap;"></div>');

	$nav.append(
		$('<button class="btn btn-sm btn-default" id="pce-prev">← Semaine précédente</button>'),
		$('<span style="font-weight:600;font-size:14px;">' + cur_label + '</span>'),
		$('<button class="btn btn-sm btn-default" id="pce-next">Semaine suivante →</button>'),
		$('<span style="flex:1;"></span>'),
		$('<button class="btn btn-sm btn-primary" id="pce-add-annexe">+ Tâche annexe</button>')
	);
	$body.append($nav);

	/* ── Légende ── */
	$body.append(
		$('<div style="display:flex;gap:16px;margin-bottom:12px;font-size:12px;">'
			+ '<span style="background:#d4edda;color:#155724;padding:2px 8px;border-radius:3px;">< 80 %</span>'
			+ '<span style="background:#fff3cd;color:#856404;padding:2px 8px;border-radius:3px;">80–100 %</span>'
			+ '<span style="background:#f8d7da;color:#721c24;padding:2px 8px;border-radius:3px;">> 100 %</span>'
			+ '<span style="color:#888;">Capacité : ' + capacity + 'h/sem.</span>'
			+ '</div>')
	);

	/* ── Table ── */
	if (!employees || employees.length === 0) {
		$body.append('<div class="text-muted" style="padding:20px 0;">'
			+ 'Aucun collaborateur avec des tâches planifiées sur cette période.</div>');
	} else {
		var header_cells = weeks.map(function (w) {
			return '<th style="text-align:center;min-width:90px;">' + w.label + '</th>';
		}).join('');

		var rows_html = employees.map(function (emp) {
			var cells = weeks.map(function (w) {
				var wd = emp.weeks[w.label] || { hours: 0, pct: 0, tasks: [] };
				var bg, fg;
				if (wd.pct < 80) {
					bg = '#d4edda'; fg = '#155724';
				} else if (wd.pct <= 100) {
					bg = '#fff3cd'; fg = '#856404';
				} else {
					bg = '#f8d7da'; fg = '#721c24';
				}
				var has_tasks = wd.tasks && wd.tasks.length > 0;
				var cursor    = has_tasks ? 'pointer' : 'default';
				var title_str = has_tasks
					? wd.tasks.map(function (t) {
						return (t.subject || '') + (t.project ? ' (' + t.project + ')' : '');
					}).join('\n')
					: '';

				return '<td data-emp="' + frappe.utils.escape_html(emp.email)
					+ '" data-week="' + frappe.utils.escape_html(w.label)
					+ '" style="background:' + bg + ';color:' + fg
					+ ';text-align:center;cursor:' + cursor
					+ ';padding:6px 4px;" title="' + frappe.utils.escape_html(title_str) + '">'
					+ (wd.hours > 0
						? wd.hours.toFixed(1) + 'h<br><small>' + wd.pct + '%</small>'
						: '<small style="color:#aaa;">—</small>')
					+ '</td>';
			}).join('');

			return '<tr><td style="font-weight:500;padding:6px 8px;white-space:nowrap;">'
				+ frappe.utils.escape_html(emp.name)
				+ '</td>' + cells + '</tr>';
		}).join('');

		var table_html =
			'<div style="overflow-x:auto;">'
			+ '<table class="table table-bordered table-sm" style="min-width:500px;">'
			+ '<thead><tr><th style="min-width:160px;">Collaborateur</th>' + header_cells + '</tr></thead>'
			+ '<tbody>' + rows_html + '</tbody>'
			+ '</table></div>';

		$body.append($(table_html));
	}

	/* ── Événements ── */

	// Navigation
	$body.find('#pce-prev').on('click', function () {
		page._pce_from_monday = _pce_shift_week(page._pce_from_monday, -1);
		_pce_refresh(page);
	});
	$body.find('#pce-next').on('click', function () {
		page._pce_from_monday = _pce_shift_week(page._pce_from_monday, 1);
		_pce_refresh(page);
	});

	// Ajouter tâche annexe
	$body.find('#pce-add-annexe').on('click', function () {
		frappe.new_doc('Annexe Task');
	});

	// Clic cellule → popup tâches
	$body.on('click', 'td[data-week]', function () {
		var week_label = $(this).data('week');
		var emp_email  = $(this).data('emp');
		var emp_data   = employees.find(function (e) { return e.email === emp_email; });
		if (!emp_data) return;
		var wd = emp_data.weeks[week_label];
		if (!wd || !wd.tasks || wd.tasks.length === 0) return;

		var task_items = wd.tasks.map(function (t) {
			var link = '/app/task/' + encodeURIComponent(t.name);
			var proj = t.project ? ' — <em>' + frappe.utils.escape_html(t.project) + '</em>' : '';
			return '<li><a href="' + link + '" target="_blank">'
				+ frappe.utils.escape_html(t.subject || t.name)
				+ '</a>' + proj + '</li>';
		}).join('');

		frappe.msgprint({
			title: frappe.utils.escape_html(emp_data.name) + ' — ' + week_label,
			message: '<ul style="margin:8px 0;padding-left:20px;">' + task_items + '</ul>',
			indicator: 'blue',
		});
	});
}
