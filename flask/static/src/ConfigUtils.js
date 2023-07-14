function populateSelect(target, values, currentOption){
    if (!target){
        return false;
    }
    else {
        const select = document.getElementById(target);
        select.innerHTML = '';

        for (var i = 0; i < values.length; i++){
            var opt = document.createElement('option');
            opt.value = values[i];
            opt.innerHTML = values[i];
            select.appendChild(opt);
        }
        select.value = currentOption;
    }
}

function updateConfigOptions(config, modelOptions) {
    populateSelect('modelSelect', modelOptions, config.summModel);
}

export default { updateConfigOptions }; 