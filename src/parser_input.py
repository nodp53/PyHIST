from argparse import ArgumentParser, RawTextHelpFormatter
import itertools as it

# TODO: Move this text elsewhere:
# '''
#     HistologySegment implements a semi-automatic pipeline to segment tissue slices
#     from the background in high resolution whole-slde histopathological images and
#     extracts patches of tissue segments from the full resolution image.

#     Whole slide histological images are very large in terms of size, making it
#     difficult for computational pipelines to process them as single units, thus,
#     they have to be divided into patches. Moreover, a significant portion of each
#     image is background, which should be excluded from downstream analyses.

#     In order to efficiently segment tissue content from each image, HistologySegment
#     utilizes a Canny edge detector and a graph-based segmentation method. A lower
#     resolution version of the image, extracted from the whole slide image file,
#     is segmented. The background is defined as the segments that can be found at the
#     borders or corners of the image (for more details check -b and -c arguments
#     documentation). Finally, patches are extracted from the full size image ,while
#     the corresponding patches are checked in the segmented image. Patches with a
#     "tissue content" greater than a threshold value (-t) are selected.

#     Moreover, segment_hist can function in test mode. This could assist the user in
#     setting the appropriate parameters for the pipeline. In test mode, segment_hist
#     will output the segmented version of the input image with scales indicating
#     the number of rows and columns. In that image the background should be separate
#     from the tissue pieces for the pipeline to work properly.
#     '''
#     REFERENCES
#     ----------
#     Felzenszwalb, P.F., & Huttenlocher, D.P. (2004). Efficient Graph-Based Image
#     Segmentation. International Journal of Computer Vision, 59, 167-181.


description_str = '''
    HistologySegment is a semi-automatic pipeline to produce image patches from
a high resolution histopathological image, either from the complete image or isolating
only the tissue in the foreground from the background.
'''

epilog_str = '''
    EXAMPLES
    --------

    Keep segmented image, save patches, produce a thumbnail with marked the
    selected patches, use a content threshold of 0.1 for patch selection.

    segment_hist -pfxt 0.1 input_image

    segment_hist -p -f -x -t 0.1 input_image

    Do not save patches, produce thumbnail, use different than the default values
    for k and m parameters.

    segment_hist -xk 10000 -m 1000 input_image

    Do not save patches, produce thumbnail, use a content threshold of 0.1 for
    patch selection, for background identification use bottom_left and top_right
    corners.

    segment_hist -xt 0.1 -b 0000 -c 0101 input_image

    Function in test mode, use different than the default values for k and m
    parameters.

    segment_hist --test -k 1000 -m 1000 input_image
    '''


def build_parser():

    parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                            description=description_str,
                            epilog=epilog_str)

    # Calculate 4-bit permutations for options that need it
    perms = list(set(
        it.permutations(['0', '0', '0', '0', '1', '1', '1', '1'], 4)))
    combs = []
    for perm in perms:
        combs.append(''.join(perm))

    # Mandatory arguments
    parser.add_argument("svs",
                        type=str,
                        help='The whole slide image input file',
                        metavar='input_image')

    # Optional argument group: execution settings
    group_exec = parser.add_argument_group('execution')
    group_exec.add_argument(
        '--patch-size',
        type=int,
        default=512,
        help='''Integer indicating the size of the produced patches. A value of D
        will produce patches of size D x D. Default value is 512.''')
    group_exec.add_argument(
        "--verbose",
        help='Print status messages at each step of the pipeline.',
        action='store_true',
        default=False)
    group_exec.add_argument(
        '--test-mode',
        help='Function in test mode',
        action='store_true',
        default=False)

    # Optional argument group: output
    group_output = parser.add_argument_group('output')
    group_output.add_argument(
        '--output',
        help="Output directory",
        type=str,
        default="output/")
    group_output.add_argument(
        '--save-tilecrossed-image',
        action='store_true',
        default=False,
        help='''Produce a thumbnail of the original image, in which the
        selected patches are marked with a cross.''')
    group_output.add_argument(
        '--save-edges',
        action='store_true',
        default=False,
        help='Keep the image produced by the Canny edge detector.')
    group_output.add_argument(
        '--save-mask',
        action='store_true',
        default=False,
        help='Keep the mask with tissue segments.')
    group_output.add_argument(
        '--save-patches',
        action='store_true',
        default=False,
        help='Save the produced patches of the full resolution image.')

    # Optional argument group: downsampling
    group_downsampling = parser.add_argument_group('downsampling')
    group_downsampling.add_argument(
        '--output-downsample',
        help='Downsampling factor for the output image.',
        type=int,
        default=16)
    group_downsampling.add_argument(
        "--downsample-mask",
        help='Downsampling factor to calculate image mask',
        type=int,
        default=16)

    # Optional argument group: segmentation
    group_segmentation = parser.add_argument_group('segmentation')
    group_segmentation.add_argument(
        '--borders',
        type=str,
        default='1111',
        help='''
        A four digit string. Each digit represents a border of the image in the
        following order: left, bottom, right, top. If the digit is equal to 1 and
        not 0, then the corresponding border will be taken into account to define
        background. For instance, with -b 1010 the algorithm will look at the left
        and right borders of the segmented image, in a window of width defined by
        the -n argument, and every segment identified will be set as background.
        If this argument is not equal to 0000, then -c should be 0000.
        Default value is 1111.''',
        choices=combs)

    group_segmentation.add_argument(
        '--corners',
        type=str,
        default='0000',
        help='''
        A four digit string. Each digit represents a corner of the image in the
        following order: top_left, bottom_left, bottom_right, top_right. If the
        digit is equal to 1 and not 0, then the corresponding corner will be taken
        into account to define background. For instane, with -c 0101 the algorithm
        will look at the bottom_left and top_right corners of the segmented image,
        in a square window of size given by the -n argument, and every segment
        identified will be set as background. If this argument is not equal to 0000,
        then -b should be 0000. Default value is 0000.''',
        choices=combs)

    group_segmentation.add_argument(
        '--k-const',
        type=int,
        default=10000,
        help='''
        Parameter required by the segmentation algorithm.
        Value for the threshold function. The threshold function controls the
        degree to which the difference between two segments must be greater than
        their internal differences in order for them not to be merged. Lower values
        result in finer segmentation. Larger images require higher values.
        Default value is 10000.''')

    group_segmentation.add_argument(
        '--minimum_segmentsize',
        type=int,
        default=10000,
        help='''Parameter required by the segmentation algorithm.
        Minimum segment size enforced by post-processing.
        Larger images require higher values.
        Default value is 10000.''')

    group_segmentation.add_argument(
        '--number-of-lines',
        type=int,
        default=100,
        help='''Integer indicating the number of lines from the borders or the corners of
        the segmented image that the algorithm should take into account to define
        background. Default value is 100.''',
        metavar='NUMBER_OF_LINES',
        dest='lines')

    group_segmentation.add_argument(
        '--sigma',
        type=float,
        default=0.5,
        help='''Parameter required by the segmentation algorithm.
        Used to smooth the input image before segmenting it.
        Default value is 0.5.''')

    group_segmentation.add_argument(
        '--content-threshold',
        type=float,
        default=0.5,
        help='''Threshold parameter indicating the proportion of a patch content that
        should not be covered by background in order to be selected. It should
        range between 0 and 1. Default value is 0.5.''',
        metavar='CONTENT_THRESHOLD',
        dest='thres')
    
    return parser