unit Tax;
{ Delphi tax unit. The probe finds no language server for Pascal/Delphi. }
interface
function VatAmount(Net: Currency): Currency;
implementation
function VatAmount(Net: Currency): Currency;
begin
  Result := Net * 0.21;
end;
end.
