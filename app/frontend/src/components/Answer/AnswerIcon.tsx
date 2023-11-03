import { Sparkle28Filled } from "@fluentui/react-icons";
import Logo from "../../assets/images/logo.png";
import styles from "./Answer.module.css";

export const AnswerIcon = () => {
    // return <Sparkle28Filled primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Answer logo" />;
    // return <Sparkle2!8Filled primaryFill={"#017cbf"} aria-hidden="true" aria-label="Answer logo" />;
    return <img src={Logo} className={styles.AnswerLogo} alt={""} />
};
