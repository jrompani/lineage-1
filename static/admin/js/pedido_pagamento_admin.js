(function() {
	// Adiciona confirmação somente quando a ação selecionada for 'confirmar_pagamentos'
	document.addEventListener('DOMContentLoaded', function() {
		var actionForm = document.getElementById('changelist-form');
		if (!actionForm) return;

		actionForm.addEventListener('submit', function(e) {
			var select = document.querySelector('select[name="action"]');
			if (!select) return;
			var action = select.value;
			if (action === 'confirmar_pagamentos') {
				var anyChecked = !!document.querySelector('input.action-select:checked');
				if (!anyChecked) return; // Sem seleção, deixa o admin lidar com a mensagem padrão
				var ok = window.confirm('Tem certeza que deseja confirmar os pagamentos selecionados? Esta ação aplicará créditos (com bônus) e marcará os pagamentos como pagos.');
				if (!ok) {
					e.preventDefault();
					return false;
				}
			}
		});
	});
})();


