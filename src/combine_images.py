from ccdproc import ImageFileCollection, Combiner, combine

def process(files_dir):
    ifc = ImageFileCollection(files_dir)

    c = Combiner(ifc.ccds())
    avg_combined = c.average_combine()

    return avg_combined
