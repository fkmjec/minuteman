import MeetingRecorder from "./MeetingRecorder";
import ApiInterface from "./ApiInterface";
import ConfigUtils from "./ConfigUtils";

// JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.ERROR);

function waitForElementLoad(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                observer.disconnect();
                resolve(document.querySelector(selector));
            }
        });

        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
    });
}

function onChunkLenSelect() {
    let chunkLen = parseFloat($("#chunkLenSelect").val());
    ApiInterface.setChunkLen(chunkLen);
}

function onModelSelect() {
    let model = $("#modelSelect").val();
    ApiInterface.setSummModel(model);
}

function populateLanguages() {
    var language_name_to_code = {
        "Hindi": "hi",
        "Chinese (Simplified)": "zh",
        "Marathi": "mt",
        // "Japan": "jp",
        // "Bulgarian": "bg",
        // "Croatian": "hr",
        "Czech": "cs",
        // "Danish": "da",
        // "Dutch": "nl",
        "English": "en",
        // "Estonian": "et",
        // "Finnish": "fi",
        "French": "fr",
        // "German": "de",
        // "Greek": "el",
        "Hungarian": "hu",
        // "Irish": "ga",
        "Italian": "it",
        // "Latvian": "lv",
        // "Lithuanian": "lt",
        // "Maltese": "mt",
        "Polish": "pl",
        "Portuguese": "pt",
        // "Romanian": "ro",
        // "Slovak": "sk",
        // "Slovenian": "sl",
        "Spanish": "es",
        // "Swedish": "sv",
        // "Albanian": "sq",
        "Arabic": "ar",
        // "Armenian": "hy",
        // "Azerbaijani": "az",
        // "Belarusian": "be",
        // "Bosnian": "bs",
        // "Georgian": "ka",
        // "Hebrew": "he",
        // "Icelandic": "is",
        // "Kazakh": "kk",
        // "Arabic (Lebanon)": "lb",
        // "Macedonian": "mk",
        // "Montenegrin": "me",
        "Russian": "ru",
        // "Serbian": "sr",
        // "Turkish": "tr",
        "Ukrainian": "uk",
        "Vietnamese": "vi",
        // "Norwegian Bokmål": "nb",
        // "Catalan": "ca",
        // "Norwegian Nynorsk": "nn"
        "Swahili": "sw",
        "Welsh": "we",
    }

    waitForElementLoad('#languageSelect').then((select) => {
        for (var language in language_name_to_code) {
            var option = document.createElement('option');
            option.value = language_name_to_code[language];
            option.text = language;
            if (language === "Czech") {
                option.selected = true;
            }
            select.add(option);
        }
    });

}

function onLanguageSelect() {
    let transcript = document.getElementsByClassName("transcript-iframe")[0];
    let summary = document.getElementsByClassName("summary-iframe")[0];

    transcript.src = transcript.src.replace(transcript.src.split("_")[1].substring(0, 2), $("#languageSelect").val());;
    summary.src = summary.src.replace(summary.src.split("_")[1].substring(0, 2), $("#languageSelect").val());;

}

let recorder = new MeetingRecorder();

$(window).bind('beforeunload', recorder.unload.bind(recorder));
$(window).bind('unload', recorder.unload.bind(recorder));
// add transcriber to global scope
window.recorder = recorder;

$(window).bind
window.onChunkLenSelect = onChunkLenSelect;
window.onModelSelect = onModelSelect;
window.onLanguageSelect = onLanguageSelect;

$(document).bind("onload", populateLanguages())

setInterval(async function () {
    try {
        let response = await ApiInterface.getState();
        ConfigUtils.updateConfigOptions(response.config, response.model_selection);
    } catch (error) {
        console.error(error.message);
    }
}, 5000);