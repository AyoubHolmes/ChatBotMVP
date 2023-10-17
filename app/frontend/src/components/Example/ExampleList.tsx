import { DocumentsListPopup } from "../DocumentsListPopup";
import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "Qu'est ce qu'un transitaire en Douane?",
        value: "Qu'est ce qu'un transitaire en Douane?"
    },
    { text: "Quels sont les tarifs des droits de Douane?", value: "Quels sont les tarifs des droits de Douane?" },
    {
        text: "Quelles sont les conditions particulières d'application de la loi douanière?",
        value: "Quelles sont les conditions particulières d'application de la loi douanière?"
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <DocumentsListPopup />
    );
};
