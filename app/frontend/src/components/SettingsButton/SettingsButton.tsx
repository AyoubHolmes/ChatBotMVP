import { Settings24Regular } from "@fluentui/react-icons";
import { Button } from "@fluentui/react-components";

import styles from "./SettingsButton.module.css";
import { FormattedMessage } from "react-intl";

interface Props {
    className?: string;
    onClick: () => void;
}

export const SettingsButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`}>
            <Button icon={<Settings24Regular />} onClick={onClick} data-testid={"developer-setting"}>
                {/* {"Developer settings"} */}
                <FormattedMessage id="translationKeys.developer-setting" />
            </Button>
        </div>
    );
};
