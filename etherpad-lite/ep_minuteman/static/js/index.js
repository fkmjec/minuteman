exports.aceAttribsToClasses = function(hook, context, cb) {
    if (context.key == "summary_seq") {
        return cb([`summary_seq::${context.value}`]);
    } else if (context.key == "trsc_seq") {
        return cb([`trsc_seq::${context.value}`]);
    }
    return cb();
}

exports.collectContentPre = (hookName, context, cb) => {
    const state = context.state;
    if (context.cls.startsWith("summary_seq::")) {
        context.cc.doAttrib(state, context.cls);
    }
    if (context.cls.startsWith("trsc_seq::")) {
        context.cc.doAttrib(state, context.cls);
    }
    return cb();
};