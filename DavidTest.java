public static void main(String[] args) throws IOException {
        extractionTest();
    }

    public static void extractionTest() throws IOException {
        InputStream in = new FileInputStream("/home/davidbneto/IdeaProjects/tabula-test/src/main/resources/carros.pdf");
        PDDocument document = PDDocument.load(in);
        SpreadsheetExtractionAlgorithm sea = new SpreadsheetExtractionAlgorithm();
        PageIterator pi = new ObjectExtractor(document).extract();
        for (int i = 0; i < 2; i++) {
            // iterate over the pages of the document
            Page page = pi.next();
            List<Table> table = sea.extract(page);
            // iterate over the tables of the page
            for (Table tables : table) {
                List<List<RectangularTextContainer>> rows = tables.getRows();
                // iterate over the rows of the table
                for (List<RectangularTextContainer> cells : rows) {
                    // print all column-cells of the row plus linefeed
                    for (RectangularTextContainer content : cells) {
                        // Note: Cell.getText() uses \r to concat text chunks
                        String text = content.getText().replace("\r", " ");
                        System.out.print(text + "|");
                    }
                    System.out.println();
                }
            }
        }

    }
