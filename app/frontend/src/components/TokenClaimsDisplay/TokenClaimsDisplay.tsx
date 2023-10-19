import { Label } from "@fluentui/react";
import { useMsal } from "@azure/msal-react";
import {
    DataGridBody,
    DataGridRow,
    DataGrid,
    DataGridHeader,
    DataGridHeaderCell,
    DataGridCell,
    createTableColumn,
    TableColumnDefinition
} from "@fluentui/react-table";
import { FormattedMessage, useIntl } from "react-intl";

type Claim = {
    name: string;
    value: string;
};

export const TokenClaimsDisplay = () => {
    const { instance } = useMsal();
    const activeAccount = instance.getActiveAccount();

    const intl = useIntl();

    const ToString = (a: string | any) => {
        if (typeof a === "string") {
            return a;
        } else {
            return JSON.stringify(a);
        }
    };

    const items: Claim[] = activeAccount?.idTokenClaims
        ? Object.keys(activeAccount.idTokenClaims).map<Claim>((key: string) => {
              return { name: key, value: ToString((activeAccount.idTokenClaims ?? {})[key]) };
          })
        : [];

    const columns: TableColumnDefinition<Claim>[] = [
        createTableColumn<Claim>({
            columnId: "name",
            compare: (a: Claim, b: Claim) => {
                return a.name.localeCompare(b.name);
            },
            renderHeaderCell: () => {
                return intl.formatMessage({ id: "translationKeys.config-content.name" });
            },
            renderCell: item => {
                return item.name;
            }
        }),
        createTableColumn<Claim>({
            columnId: "value",
            compare: (a: Claim, b: Claim) => {
                return a.value.localeCompare(b.value);
            },
            renderHeaderCell: () => {
                return intl.formatMessage({ id: "translationKeys.config-content.value" });
            },
            renderCell: item => {
                return item.value;
            }
        })
    ];

    return (
        <div>
            {/* <Label>
                <FormattedMessage id="translationKeys.config-content.id-token-claims" />
            </Label>
            <DataGrid items={items} columns={columns} sortable getRowId={item => item.name}>
                <DataGridHeader>
                    <DataGridRow>{({ renderHeaderCell }) => <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>}</DataGridRow>
                </DataGridHeader>
                <DataGridBody<Claim>>
                    {({ item, rowId }) => <DataGridRow<Claim> key={rowId}>{({ renderCell }) => <DataGridCell>{renderCell(item)}</DataGridCell>}</DataGridRow>}
                </DataGridBody>
            </DataGrid> */}
        </div>
    );
};
