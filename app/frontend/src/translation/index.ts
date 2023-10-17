import flattenMessages from "./utils";
import frMessages from "./fr";
import enMessages from "./en";

export const intlMessages = {
    fr: flattenMessages(frMessages),
    en: flattenMessages(enMessages)
};
