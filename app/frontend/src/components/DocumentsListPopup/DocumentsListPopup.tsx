import React, { useState } from "react";
import styles from "./DocumentsListPopup.module.css";
import { FormattedMessage } from "react-intl";

const DocumentsListPopup: React.FC = () => {
    const [isOpen, setIsOpen] = useState<boolean>(false);
    return (
        <div className={styles.popupUpWrapper}>
            <button type="button" className={styles.popUpButton} onClick={() => setIsOpen(true)}>
                <FormattedMessage id={"translationKeys.document-popup-button"} />
            </button>
            {isOpen && (
                <div className={styles.popupUp}>
                    <div onClick={() => setIsOpen(false)} className={styles.popupUpBg}></div>
                    <div className={styles.popUpModel}>
                        <div className={styles.popUpModelTitle}>
                            <FormattedMessage id={"translationKeys.document-popup-button"} />:
                        </div>
                        <div className={styles.popUpMdelDocumentName}>Code des douanes et impoôts indirects 2023</div>
                        <div className={styles.popUpMdelDocumentName}>DocScan obligations et droits du transitaire en douane</div>
                        <div className={styles.popUpMdelDocumentName}>Formulaire BP Paytracker Version Entreprises</div>
                        <div className={styles.popUpMdelDocumentName}>Formulaire BP PayTracker Version Particuliers</div>
                        <div className={styles.popUpMdelDocumentName}>swift cat7 advanceinformation feb2022</div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DocumentsListPopup;
