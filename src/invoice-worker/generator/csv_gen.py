import csv

def generate(data, output_path):
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['ITEM #', 'DESCRIPTION', 'QTY', 'UNIT PRICE', 'TOTAL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Basic metadata at the top could be added but CSV is strictly tabular
        # For industry grade CSV, we'll include header info as rows or just the table
        
        # Header Info as rows
        csvfile.write(f"INVOICE #: {data.get('invoice_no', '')}\n")
        csvfile.write(f"DATE: {data.get('date', '')}\n")
        csvfile.write(f"COMPANY: {data.get('company_name', '')}\n")
        csvfile.write("\n")
        
        writer.writeheader()
        for item in data.get('items', []):
            writer.writerow({
                'ITEM #': item.get('id', ''),
                'DESCRIPTION': item.get('description', ''),
                'QTY': item.get('qty', 0),
                'UNIT PRICE': item.get('unit_price', 0.0),
                'TOTAL': item.get('total', 0.0)
            })
        
        csvfile.write("\n")
        csvfile.write(f"SUBTOTAL,,,{data.get('subtotal', 0.0)}\n")
        csvfile.write(f"TAX RATE,,,{data.get('tax_rate', 0.0)}\n")
        csvfile.write(f"TOTAL,,,{data.get('total_amount', 0.0)}\n")
