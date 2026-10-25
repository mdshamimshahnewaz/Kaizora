document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('select[data-searchable]').forEach(select => {
    const input = document.createElement('input');
    input.type = 'search';
    input.placeholder = 'Search by name or username';
    input.setAttribute('aria-label', 'Search ' + (select.labels[0]?.textContent || 'choices'));
    const options = [...select.options].map(option => option.cloneNode(true));
    select.before(input);
    input.addEventListener('input', () => {
      const selected = select.value;
      const query = input.value.toLocaleLowerCase();
      select.replaceChildren(...options.filter(option => !option.value || option.value === selected || option.textContent.toLocaleLowerCase().includes(query)).map(option => option.cloneNode(true)));
      select.value = selected;
    });
  });
});
