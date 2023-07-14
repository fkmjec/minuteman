function populateSelect(target, values, currentOption){
    const select = document.getElementById(target);
    if (select === document.activeElement) {
        return;
    }
    select.innerHTML = '';

    for (var i = 0; i < values.length; i++){
        var opt = document.createElement('option');
        opt.value = values[i];
        opt.innerHTML = values[i];
        select.appendChild(opt);
    }
    select.value = currentOption;
}

function updateChunkLen(chunkLen) {
    const element = document.getElementById("chunkLenSelect"); 
    if (element !== document.activeElement) {
        element.value = chunkLen;
    }
}

function updateConfigOptions(config, modelOptions) {
    populateSelect('modelSelect', modelOptions, config.summModel);
    updateChunkLen(config.chunkLen);
}

export default { updateConfigOptions }; 