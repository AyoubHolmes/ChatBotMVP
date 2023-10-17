import { Outlet, NavLink, Link } from "react-router-dom";

import github from "../../assets/github.svg";

import styles from "./Layout.module.css";

import { useLogin } from "../../authConfig";

import { LoginButton } from "../../components/LoginButton";
import { LANGUAGES, useLanguageContext } from "../../context";
import { IntlProvider } from "react-intl";
import { FlattenedDictionary } from "../../translation/utils";
import { intlMessages } from "../../translation";

export const intlMessagesDispatcher: Record<LANGUAGES, FlattenedDictionary> = {
    [LANGUAGES.FR]: intlMessages.fr,
    [LANGUAGES.EN]: intlMessages.en
};

const Layout = () => {
    const { language } = useLanguageContext();
    return (
        <IntlProvider locale={language} messages={intlMessagesDispatcher[language]}>
            <div className={styles.layout}>
                <header className={styles.header} role={"banner"}>
                    <div className={styles.headerContainer}>
                        <Link to="/" className={styles.headerTitleContainer}>
                            <h3 className={styles.headerTitle}>BCP | Trade Chatbot</h3>
                        </Link>
                        {useLogin && <LoginButton />}
                    </div>
                </header>

                <Outlet />
            </div>
        </IntlProvider>
    );
};

export default Layout;
